import requests
import sys

def nom_geocode(query):
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

def _to_readable_addr(addr_obj):
  addr_str = ""
  if 'road' in addr_obj.keys():
    addr_str += addr_obj['road']

  if 'suburb' in addr_obj.keys():
    addr_str += ', ' + addr_obj['suburb']
  elif 'town' in addr_obj.keys():
    addr_str += ', ' + addr_obj['town']

  return addr_str

def nom_reverse_geocode(lat, lng):
  url_template = ' https://nominatim.openstreetmap.org/reverse?format=json&lat={0}&lon={1}&zoom=18&addressdetails=1'
  url = url_template.format(lat, lng)
  response = requests.get(url, timeout=60)

  geo_result = {
    "success": True,
    "lat": lat,
    "lng": lng
  }

  if response.status_code is not 200:
    geo_result['success'] = False
    geo_result['msg'] = "Failed to return a results for lat:{} lng:{}".format(lat, lng)
    return geo_result
  
  result = response.json()

  if result and 'lat' in result:
    geo_result['display_name'] = result['display_name']
    geo_result['address'] = _to_readable_addr(result['address'])

  return geo_result
