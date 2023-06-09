import spotipy
from spotipy.oauth2 import SpotifyOAuth
import colorama
from colorama import Fore, Style
import json

colorama.init(autoreset=True)

# Set up your Spotify API credentials
client_id = 'YOUR_CLIENT_ID'
client_secret = 'YOUR_CLIENT_SECRET'
redirect_uri = 'http://localhost:8888/callback'
scope = 'playlist-modify-public playlist-read-private playlist-modify-private'  # Add 'playlist-modify-private' scope


# Load the access token from a file
try:
    with open('access_token.json', 'r') as file:
        token_info = json.load(file)
except FileNotFoundError:
    token_info = None

if token_info is None or 'access_token' not in token_info:
    # Create an instance of SpotifyOAuth and prompt user authorization
    sp_oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)
    auth_url = sp_oauth.get_authorize_url()
    print(f"{Style.BRIGHT}Please visit this URL to authorize your application: {Fore.BLUE}{auth_url}")
    response = input("Enter the URL you were redirected to: ")
    code = sp_oauth.parse_response_code(response)
    token_info = sp_oauth.get_access_token(code)

    if 'access_token' in token_info:
        # Save the access token to a file
        with open('access_token.json', 'w') as file:
            json.dump(token_info, file)
    else:
        print(f"{Fore.RED}Token retrieval failed. Please try again.")

# Extract the access token from token_info
access_token = token_info['access_token']

# Create a Spotify API client
sp = spotipy.Spotify(auth=access_token)

# Function to create a playlist with an artist
def create_playlist_with_artist():
    print(f"\n{Style.BRIGHT}--- Create a Playlist with an Artist ---")
    playlist_name = input("Enter the playlist name: ")
    artist_name = input("Enter the artist's name: ")

    # Search for the artist
    results = sp.search(q=artist_name, type='artist', limit=1)
    items = results['artists']['items']

    if len(items) > 0:
        artist = items[0]
        artist_id = artist['id']
        print(f"{Fore.GREEN}Artist found: {Style.RESET_ALL}{artist['name']}")
    else:
        print(f"{Fore.RED}No artist found with that name.")
        return

    # Get all tracks by the artist (as a primary artist)
    tracks = sp.artist_top_tracks(artist_id)['tracks']

    # Search for tracks where the artist is featured
    query = f'artist:"{artist["name"]}"'
    results = sp.search(q=query, type='track', limit=50)
    featured_tracks = results['tracks']['items']

    # Combine the two sets of tracks
    all_tracks = tracks + featured_tracks

    # Create an empty list to store the track URIs
    track_uris = [track['uri'] for track in all_tracks]

    # Create a new playlist
    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, playlist_name)

    # Add the track URIs to the playlist
    for i in range(0, len(track_uris), 100):
        sp.user_playlist_add_tracks(user_id, playlist['id'], track_uris[i:i+100])

    print(f"{Fore.GREEN}Playlist created successfully!")

    # Retrieve playlist information
    playlist_info = sp.playlist(playlist['id'])
    total_tracks = playlist_info['tracks']['total']
    playlist_duration = sum([track['track']['duration_ms'] for track in playlist_info['tracks']['items']])

    print(f"{Fore.YELLOW}Number of songs added: {total_tracks}")
    duration_seconds = playlist_duration // 1000
    duration_minutes, duration_seconds = divmod(duration_seconds, 60)
    duration_hours, duration_minutes = divmod(duration_minutes, 60)
    print(f"{Fore.YELLOW}Playlist duration: {duration_hours} hours, {duration_minutes} minutes, {duration_seconds} seconds")

# Function to delete playlists
def delete_playlists():
    print(f"\n{Style.BRIGHT}--- Delete Playlists ---")
    user_id = sp.current_user()['id']

    # Get user's playlists
    playlists = sp.current_user_playlists()['items']

    if len(playlists) == 0:
        print(f"{Fore.YELLOW}You have no playlists to delete.")
        return

    print(f"{Fore.LIGHTYELLOW_EX}Your Playlists:")
    for i, playlist in enumerate(playlists):
        print(f"{Fore.LIGHTCYAN_EX}{i + 1}. {Style.RESET_ALL}{playlist['name']}")

    # Select the playlist to delete
    while True:
        playlist_num = input(f"Enter the number of the playlist to delete (1-{len(playlists)}): ")
        if not playlist_num.isdigit():
            print(f"{Fore.RED}Invalid input. Please enter a number.")
            continue
        playlist_num = int(playlist_num)
        if not 1 <= playlist_num <= len(playlists):
            print(f"{Fore.RED}Invalid input. Please enter a number between 1 and {len(playlists)}.")
            continue
        break

    playlist_to_delete = playlists[playlist_num - 1]
    playlist_name = playlist_to_delete['name']
    playlist_id = playlist_to_delete['id']

    # Delete the playlist
    sp.user_playlist_unfollow(user_id, playlist_id)
    print(f"{Fore.GREEN}Playlist '{playlist_name}' deleted successfully!")

# Menu selection
while True:
    print(f"\n{Style.BRIGHT}--- {Fore.GREEN}Spotify Playlist Manager ---")
    print(f"{Fore.LIGHTBLUE_EX}1. {Style.RESET_ALL}Create a playlist with an artist")
    print(f"{Fore.LIGHTBLUE_EX}2. {Style.RESET_ALL}Create a playlist with a genre")
    print(f"{Fore.LIGHTBLUE_EX}3. {Style.RESET_ALL}Delete playlists")
    print(f"{Fore.LIGHTBLUE_EX}4. {Style.RESET_ALL}Exit")

    choice = input(f"Enter your choice ({Fore.LIGHTWHITE_EX}{Style.BRIGHT}1{Style.RESET_ALL}, {Fore.LIGHTWHITE_EX}{Style.BRIGHT}2{Style.RESET_ALL}, {Fore.LIGHTWHITE_EX}{Style.BRIGHT}3{Style.RESET_ALL}, or {Fore.LIGHTWHITE_EX}{Style.BRIGHT}4{Style.RESET_ALL}): ")

    if choice == '1':
        create_playlist_with_artist()

    elif choice == '2':
        # Create a playlist with a genre
        print(f"\n{Style.BRIGHT}--- {Fore.GREEN}Create a Playlist with a Genre ---")
        playlist_name = input("Enter the playlist name: ")
        genre_name = input("Enter the genre name: ")

        # Search for tracks based on the genre
        results = sp.search(q=f"genre:{genre_name}", type='track', limit=50)
        tracks = results['tracks']['items']

        if len(tracks) == 0:
            print(f"{Fore.RED}No tracks found for the genre: {genre_name}")
            continue

        print(f"{Fore.YELLOW}{len(tracks)} songs with the genre '{genre_name}' added to the playlist.")

        # Create a new playlist
        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(user_id, playlist_name)

        # Add the track URIs to the playlist
        track_uris = [track['uri'] for track in tracks]
        artist_names = [track['artists'][0]['name'] for track in tracks]

        print(f"{Fore.YELLOW}Here are some of the artists added: {', '.join(artist_names[:6])}")

        sp.user_playlist_add_tracks(user_id, playlist['id'], track_uris)

        print(f"{Fore.GREEN}Playlist created successfully!")

        # Retrieve playlist information
        playlist_info = sp.playlist(playlist['id'])
        total_tracks = playlist_info['tracks']['total']
        playlist_duration = sum([track['track']['duration_ms'] for track in playlist_info['tracks']['items']])

        print(f"{Fore.YELLOW}Number of songs added: {total_tracks}")
        duration_seconds = playlist_duration // 1000
        duration_minutes, duration_seconds = divmod(duration_seconds, 60)
        duration_hours, duration_minutes = divmod(duration_minutes, 60)
        print(f"{Fore.YELLOW}Playlist duration: {duration_hours} hours, {duration_minutes} minutes, {duration_seconds} seconds")

    elif choice == '3':
        delete_playlists()

    elif choice == '4':
        # Exit the program
        print(f"{Fore.GREEN}Exiting...")
        break

    else:
        print(f"{Fore.RED}Invalid choice. Please try again.")
        continue