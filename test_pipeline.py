import requests

# Test English
print("=== Testing English TTS ===")
res = requests.post('http://localhost:8001/api/live-interview/start', json={
    'candidate_name': 'Test',
    'exam': 'SSC CGL',
    'subject': 'General Awareness',
    'language': 'English'
})
data = res.json()
print('Status:', res.status_code)
print('Audio URL:', data.get('audio_url'))
if data.get('audio_url'):
    ar = requests.get('http://localhost:8001' + data['audio_url'])
    print('Audio:', ar.status_code, len(ar.content), 'bytes')

# Test Hindi
print("\n=== Testing Hindi TTS ===")
res2 = requests.post('http://localhost:8001/api/live-interview/start', json={
    'candidate_name': 'Test',
    'exam': 'SSC CGL',
    'subject': 'General Awareness',
    'language': 'Hindi'
})
data2 = res2.json()
print('Status:', res2.status_code)
print('Audio URL:', data2.get('audio_url'))
print('Language:', data2.get('candidate', {}).get('language'))
if data2.get('audio_url'):
    ar2 = requests.get('http://localhost:8001' + data2['audio_url'])
    print('Audio:', ar2.status_code, len(ar2.content), 'bytes')
else:
    print('ERROR - No audio_url!')
    print('Full response:', data2)
