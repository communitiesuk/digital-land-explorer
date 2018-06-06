import requests

def nomgeocode(query):
  # send the query to the nominatim geocoder and parse the json response
  url_template = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=gb&q={}'
  url = url_template.format(query)
  response = requests.get(url, timeout=60)
  results = response.json()

  geo_result = {
    "success": True,
    "query": query
  }

  # if results were returned, parse lat and long out of the result
  if len(results) > 0 and 'lat' in results[0] and 'lon' in results[0]:
    geo_result['lat'] = float(results[0]['lat'])
    geo_result['lng'] = float(results[0]['lon'])
    geo_result['display_name'] = results[0]['display_name']
  else:
    geo_result['success'] = False
    geo_result['msg'] = "Failed to return lat/lng for query:{}".format(query)

  return geo_result