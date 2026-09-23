import os
import boto3
import json
from botocore.exceptions import ClientError
import requests
from datetime import datetime, timedelta
from aired_alert import new_ep_html, new_ep_text, new_movie_html, new_movie_text

secretsmanager_client = boto3.client('secretsmanager')
lambda_client = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')

def get_secret(secret_name):
    try:
        return secretsmanager_client.get_secret_value(SecretId=secret_name)['SecretString']
    except ClientError as e:
        print(f"Error retrieving secret '{secret_name}': {e}")
        raise e

def invoke_ses_sender_lambda(recipient_email, subject, body_html, body_text):
    try:
        response = lambda_client.invoke(
            FunctionName=os.environ.get('SES_SENDER_LAMBDA_NAME'),
            InvocationType='Event',
            Payload=json.dumps({"recipient_email": recipient_email, "subject": subject, "body_html": body_html, "body_text": body_text})
        )
        return response.get('StatusCode') == 202
    except ClientError as e:
        print(f"Error invoking SES Sender Lambda for {recipient_email}: {e}")
        return False

def get_movie_streaming_availability(tmdb_id, headers):
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers",
        headers=headers,
        timeout=10
    )
    response.raise_for_status()

    eligible_types = ('flatrate', 'free', 'ads', 'rent', 'buy')
    results = response.json().get('results') or {}
    providers_by_region = {}
    tmdb_link = None

    for region_code, region_data in results.items():
        provider_names = set()
        for availability_type in eligible_types:
            for provider in region_data.get(availability_type, []):
                name = provider.get('provider_name')
                if name:
                    provider_names.add(name)
        if provider_names:
            providers_by_region[region_code] = sorted(provider_names)
            if tmdb_link is None:
                tmdb_link = region_data.get('link')

    return providers_by_region, tmdb_link

def lambda_handler(event, context):
    tmdb_api_key = get_secret(os.environ.get('TMDB_API_SECRET_NAME'))
    yesterday_utc = (datetime.utcnow() - timedelta(days=1)).date()

    subscriptions = []
    last_evaluated_key = None
    while True:
        try:
            response = dynamodb_client.scan(TableName=os.environ.get('DYNAMODB_TABLE_NAME'), ExclusiveStartKey=last_evaluated_key) if last_evaluated_key else dynamodb_client.scan(TableName=os.environ.get('DYNAMODB_TABLE_NAME'))
            subscriptions.extend(response.get('Items', []))
            if not response.get('LastEvaluatedKey'):
                break
            last_evaluated_key = response['LastEvaluatedKey']
        except ClientError as e:
            print(f"DynamoDB scan failed: {e}")
            return {'statusCode': 500, 'body': json.dumps(f"Error scanning DynamoDB: {e.response['Error']['Message']}")}

    for item in subscriptions:
        user_email = item['user_email']['S']
        tmdb_full_slug = item['tmdb_id']['S']
        is_movie = tmdb_full_slug.startswith('movie:')
        tmdb_slug = tmdb_full_slug.split(':', 1)[1] if is_movie else tmdb_full_slug

        try:
            tmdb_numeric_id = tmdb_slug.split('-')[0]
            if not tmdb_numeric_id.isdigit(): raise ValueError
        except Exception as e:
            print(f"Error processing subscription {tmdb_full_slug}: {e}")
            continue

        headers = {"Authorization": f"Bearer {tmdb_api_key}", "accept": "application/json"}
        
        try:
            if is_movie:
                providers_by_region, tmdb_link = get_movie_streaming_availability(tmdb_numeric_id, headers)
                if not providers_by_region:
                    continue

                details_response = requests.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_numeric_id}?language=en-US",
                    headers=headers,
                    timeout=10
                )
                details_response.raise_for_status()
                movie_data = details_response.json()
                movie_title = movie_data.get('title', 'Unknown Movie')
                poster_path = movie_data.get('poster_path')
                image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                tmdb_link = tmdb_link or f"https://www.themoviedb.org/movie/{tmdb_slug}"

                accepted = invoke_ses_sender_lambda(
                    user_email,
                    f"Now streaming: {movie_title}",
                    new_movie_html(movie_title, image_url, tmdb_link, providers_by_region),
                    new_movie_text(movie_title, tmdb_link, providers_by_region)
                )
                if accepted:
                    try:
                        dynamodb_client.delete_item(
                            TableName=os.environ.get('DYNAMODB_TABLE_NAME'),
                            Key={
                                'user_email': {'S': user_email},
                                'tmdb_id': {'S': tmdb_full_slug}
                            }
                        )
                        print(f"Queued movie streaming alert and removed subscription: {tmdb_slug}")
                    except ClientError as e:
                        print(f"Could not remove completed movie subscription for {user_email}: {e}")
                continue

            response = requests.get(f"https://api.themoviedb.org/3/tv/{tmdb_numeric_id}?language=en-US", headers=headers, timeout=10)
            response.raise_for_status()
            tmdb_data = response.json()

            if tmdb_data.get('last_episode_to_air') and datetime.strptime(tmdb_data['last_episode_to_air']['air_date'], '%Y-%m-%d').date() == yesterday_utc:
                episode_info = tmdb_data['last_episode_to_air']
                show_name = tmdb_data.get('name', 'Unknown TV Show')
                season_number = episode_info.get('season_number', 'N/A')
                episode_number = episode_info.get('episode_number', 'N/A')
                episode_name = episode_info.get('name', 'N/A')
                poster_path = tmdb_data.get('poster_path')
                image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                tmdb_url = f"https://www.themoviedb.org/tv/{tmdb_slug}"

                invoke_ses_sender_lambda(
                    user_email,
                    f"New Episode of {show_name} - S{season_number}E{episode_number} {episode_name}",
                    new_ep_html(show_name, season_number, episode_number, episode_name, image_url, tmdb_url),
                    new_ep_text(show_name, season_number, episode_number, episode_name, tmdb_url) 
                )

        except requests.exceptions.RequestException as e:
            print(f"Data not found in fetch API: {e}")
        except Exception:
            continue

    return {'statusCode': 200, 'body': json.dumps('TMDB Scanner Lambda execution finished.')}
