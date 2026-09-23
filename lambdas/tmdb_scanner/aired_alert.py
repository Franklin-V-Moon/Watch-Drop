from html import escape


def new_ep_html(show_name, season_number, episode_number, episode_name, image_url, tmdb_url):
    return f"""
<html>
<body style="text-align: center;">
    <h1 style="text-align: center; margin-bottom: 30px;">💧</h1>
    <h2 style="text-align: center; margin: 0; padding: 0;">{show_name} - {episode_name}</h2>
    <h2 style="text-align: center;">Season {season_number} - Episode {episode_number}</h2>
    
    <p style="text-align: center;">Enjoy your Watch Drop!</p>
    <p style="text-align: center; margin-bottom: 50px;">Find more shows on <a href="https://www.themoviedb.org/">The Movie Database</a></p>

    <img src="{image_url}" alt="{show_name} Poster" style="max-width: 50%; height: auto; display: block; margin: 0 auto 50px;">
    
    <a href="mailto:subscribe@watchdrop.org?subject=remove%20{tmdb_url}" style="color: #FF5733;">Unsubscribe from this alert</a>
    <p></p>
    <a href="mailto:subscribe@watchdrop.org?subject=nuke%20account" style="color: #FF5733; font-weight: bold;">Unsubscribe ALL</a>
    
    <p>For support, email us at franklin.v.moon@gmail.com</p>

    <hr style="margin: 30px 0;">
    <p style="font-weight: bold;">Want alerts for another title?</p>
    <p>Find its TV show or movie page on <a href="https://www.themoviedb.org/">TMDB</a>, then email the link to
    <a href="mailto:subscribe@watchdrop.org?subject=add">subscribe@watchdrop.org</a> or
    <a href="mailto:WatchDrop@watchdrop.org?subject=add">WatchDrop@watchdrop.org</a>
    with the subject <code>add &lt;TMDB link&gt;</code>.</p>
    <p>To remove a show, use <code>remove &lt;TMDB link&gt;</code> as the subject.</p>
</body>
</html>
"""

def new_ep_text(show_name, season_number, episode_number, episode_name, tmdb_url):
    return f"""
{show_name} - {episode_name}
Season {season_number} - Episode {episode_number}

Enjoy your Watch Drop!
From the Watch Drop team

Unsubscribe from this alert: mailto:subscribe@watchdrop.org?subject=remove%20{tmdb_url}
Unsubscribe ALL: mailto:subscribe@watchdrop.org?subject=nuke%20account

For support, email us at franklin.v.moon@gmail.com

Want alerts for another title?
Find its TV show or movie page at https://www.themoviedb.org/, then email the link to
subscribe@watchdrop.org or WatchDrop@watchdrop.org with the subject: add <TMDB link>

To remove a show, use this subject: remove <TMDB link>
"""


def _movie_availability_summary(providers_by_region):
    providers = sorted({
        provider
        for provider_names in providers_by_region.values()
        for provider in provider_names
    })
    regions = sorted(providers_by_region)
    region_summary = ", ".join(regions[:12])
    if len(regions) > 12:
        region_summary += f", and {len(regions) - 12} more"
    return providers, region_summary


def new_movie_html(movie_title, image_url, tmdb_url, providers_by_region):
    providers, regions = _movie_availability_summary(providers_by_region)
    provider_list = ", ".join(escape(provider) for provider in providers)
    return f"""
<html>
<body style="text-align: center; font-family: Arial, sans-serif;">
    <h1 style="margin-bottom: 20px;">💧</h1>
    <h2>Now available to stream: {escape(movie_title)}</h2>
    <p>Streaming options reported in: {escape(regions)}</p>
    <p>Providers: {provider_list}</p>
    <img src="{escape(image_url, quote=True)}" alt="{escape(movie_title)} poster" style="max-width: 50%; height: auto; display: block; margin: 25px auto;">
    <p><a href="{escape(tmdb_url, quote=True)}">See availability on TMDB</a></p>
    <p style="font-size: 12px;">Streaming availability data provided by JustWatch via TMDB.</p>
    <p>This one-time movie alert is complete. To watch another movie, email
    <a href="mailto:subscribe@watchdrop.org?subject=add">subscribe@watchdrop.org</a> or
    <a href="mailto:WatchDrop@watchdrop.org?subject=add">WatchDrop@watchdrop.org</a> with the subject<br>
    <code>add https://www.themoviedb.org/movie/550-fight-club</code>.</p>
    <p>To cancel a pending movie alert, use the subject<br><code>remove &lt;TMDB movie link&gt;</code>.</p>
</body>
</html>
"""


def new_movie_text(movie_title, tmdb_url, providers_by_region):
    providers, regions = _movie_availability_summary(providers_by_region)
    return f"""
Now available to stream: {movie_title}

Reported regions: {regions}
Providers: {', '.join(providers)}

See availability on TMDB: {tmdb_url}
Streaming availability data provided by JustWatch via TMDB.

This one-time movie alert is complete. To watch another movie, email
subscribe@watchdrop.org or WatchDrop@watchdrop.org with the subject:
add https://www.themoviedb.org/movie/550-fight-club

To cancel a pending movie alert, use the subject: remove <TMDB movie link>
"""
