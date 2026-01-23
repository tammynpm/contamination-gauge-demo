import requests
import io
from PIL import Image, ImageDraw


def create_test_image(contamination_level="clean"):
    img=Image.new('RGB', (800,600), color='white')
    draw=ImageDraw.Draw(img)

    if contamination_level=="dirty":
        import random
        for _ in range(100):
            x=random.randint(0,800)
            y=random.randint(0,600)
            r=random.randint(5,20)
            draw.ellipse([x-r,y-r,x+r,y+r], fill='gray')
    elif contamination_level=="moderate":
        for _ in range(30):
            x=random.randint(0,800)
            y=random.randint(0,600)
            r=random.randint(5,15)
            draw.ellipse([x-r,y-r,x+r,y+r], fill='lightgray')

    img_bytes = io.BytesIO() #create a bytesIO object
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0) # cursor was at teh end of written data, reposition cursor
    return img_bytes


def test_analyze_endpoint():
    url = "http://localhost:8000/analyze"
    print("testing clean image")
    clean_img = create_test_image("clean")
    files ={'image': ('clean.png', clean_img, 'image/png')}
    data = {
        'baseline_id': 'clean_surface', 
        'sample_name': 'Test clean',
        'location': 'lab bench A'
    }

    response =requests.post(url, files=files, data=data)
    print(f"status: {response.status_code}")
    print(f"response: {response.json()}\n")

def test_baselines_endpoints():
    url="http://localhost:8000/baselines"
    print("testing baselines")
    response=requests.get(url)
    print(f"baselines: {response.json()}\n")

if __name__=="__main__":
    test_analyze_endpoint()
    test_baselines_endpoints()
