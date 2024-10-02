import requests
import os
import json

def download_manga_cover(manga_name):
    manga_name_encoded = manga_name.replace(" ", "%20")
    search_url = f"https://api.mangadex.org/manga?title={manga_name_encoded}"
    print(f"Recherche de '{manga_name}'...")
    print(f"URL : {search_url}")

    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        if not data['data']:
            print(f"Aucun résultat trouvé pour '{manga_name}'.")
            return

        manga_info = data['data'][0]
        manga_id = manga_info['id']

        # ? save info
        manga_details = {
            "title": manga_info['attributes'].get('title', {}).get('en', 'N/A'),
            "alternative_titles": [alt_title.get('en', 'N/A') for alt_title in manga_info['attributes'].get('altTitles', [])],
            "description": manga_info['attributes'].get('description', {}).get('en', 'N/A'),
            "genres": [],
            "themes": [],
            "publication_year": manga_info['attributes'].get('year', 'N/A'),
            "status": manga_info['attributes'].get('status', 'N/A'),
            "cover_image_url": None,
            "alternative_images": []
        }

        for tag in manga_info['attributes'].get('tags', []):
            tag_name = tag['attributes'].get('name', {}).get('en', 'N/A')
            if tag['type'] == 'tag':
                manga_details["genres"].append(tag_name)
            elif tag['type'] == 'theme':
                manga_details["themes"].append(tag_name)

        cover_art_relationships = manga_info['relationships']
        cover_id = next((rel['id'] for rel in cover_art_relationships if rel['type'] == 'cover_art'), None)

        if cover_id:
            cover_url = f"https://api.mangadex.org/cover/{cover_id}"
            cover_response = requests.get(cover_url)
            cover_response.raise_for_status()
            cover_data = cover_response.json()
            cover_filename = cover_data['data']['attributes'].get('fileName', None)

            if cover_filename:
                manga_details["cover_image_url"] = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}"

                img_response = requests.get(manga_details["cover_image_url"])
                img_response.raise_for_status()

                os.makedirs(f'static/meta/{manga_name}', exist_ok=True)

                image_path = os.path.join(f'static/meta/{manga_name}', f"{manga_name}.jpg")
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)

                print(f"Couverture téléchargée : {image_path}")
            else:
                print(f"Aucune couverture disponible pour '{manga_name}'.")
                return
        else:
            print(f"Aucune couverture trouvée pour '{manga_name}'.")
            return

        for relationship in cover_art_relationships:
            if relationship['type'] != 'cover_art':
                try:
                    alt_cover_url = f"https://api.mangadex.org/cover/{relationship['id']}"
                    alt_cover_response = requests.get(alt_cover_url)
                    alt_cover_response.raise_for_status()
                    alt_cover_data = alt_cover_response.json()
                    alt_cover_filename = alt_cover_data['data']['attributes'].get('fileName', None)

                    if alt_cover_filename:
                        alternative_image_url = f"https://uploads.mangadex.org/covers/{manga_id}/{alt_cover_filename}"
                        manga_details["alternative_images"].append(alternative_image_url)
                except requests.exceptions.RequestException as e:
                    print(f"Erreur lors de l'obtention d'une image alternative : {e}")

        json_filename = os.path.join(f'static/meta/{manga_name}', f"{manga_name}.json")
        with open(json_filename, 'w', encoding='utf-8') as json_file:
            json.dump(manga_details, json_file, ensure_ascii=False, indent=4)

        print(f"Détails sauvegardés dans : {json_filename}")

    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP : {http_err}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")