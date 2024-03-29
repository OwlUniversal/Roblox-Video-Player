
import json
import threading
import time,os
from yt_dlp import YoutubeDL
import cv2
from PIL import Image, ImageOps
import ngrok_library
from flask import Flask, jsonify, request, render_template

app = Flask(__name__,static_url_path='')
ngrok_library.run_with_ngrok(app)
arr = {}
def imagetopixel(image,id,pos,sizes="200x100"):
  global arr
  arr[id][pos] = "nil"
  t = time.time()
  sizes = sizes.split("x")

  cv2_im = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

  snapshot = Image.fromarray(cv2_im)
  snapshot = snapshot.resize((int(sizes[0]),int(sizes[1])))
  snapshot = ImageOps.mirror(snapshot)
  pixels = snapshot.load()
  width, height = snapshot.size
  all_pixels = []
  all_pixels.append(f"video;{str(width)}x{str(height)};")
  for x in range(width):
      for y in range(height):
          cpixel = pixels[x, y]
          cpixel = str(cpixel)
          cpixel = cpixel.replace("(","").replace(")","").replace(" ","")
          all_pixels.append(cpixel+";")
  snapshot.close()
  arr[id][pos] = ''.join(str(x) for x in all_pixels)

@app.route('/reset', methods=['POST'])
def reset():
    global arr
    arr = {}
    return "a"

@app.route('/play/<id>', methods=['POST'])
def getframes(id):
    global arr
    if id in arr and arr[id].__len__() != 0:
        newarr = []
        count = 0
        for v in range(0,10):
           if arr[id].__len__()-1 == 0 :
              break
           newarr.append(arr[id][0])
           del arr[id][0]
           count+=1
        return newarr
    else:
        return "False"

@app.route('/', methods=['POST'])
def result():
    global arr
    url = request.json["url"]
    frameskip = request.json["frameskip"]
    smartframes = request.json["settings"]["fastframe"]

    name = ""
    ydl_opts = {'outtmpl': ''}
    with YoutubeDL() as ydl:
        info = ydl.extract_info(url,download=False)
        name = info["id"]
        ydl_opts["outtmpl"] = name

    if name in arr:
        return name
    with YoutubeDL(ydl_opts) as ydl:
        if not os.path.exists(f"{name}.webm"):
          ydl.download(url)

    if os.path.exists(name):
        os.rename(name,name+".webm")
    elif os.path.exists(name+".mkv"):
        os.rename(name+".mkv",name+".webm")
    vidcap = cv2.VideoCapture(f'{name}.webm')
    #vidcap.get(cv2.CAP_PROP_FRAME_WIDTH,)
    success,image = vidcap.read()
    skip = 0
    count = 0
    arr[name] = {}
    while success:
        if skip != frameskip:
            skip += 1
            success,image = vidcap.read()
            continue

      
        threading.Thread(target=imagetopixel,args=(image,name,arr[name].__len__())).start()
        #arr[name].append(imagetopixel(pil_im).replace(" ",""))
        success,image = vidcap.read()
        skip = 0
        count += 1

    if smartframes:
     time.sleep(5)
    else:
     for v in arr[name]:
        v = arr[name][v]
        if v == "nil":
            while v == "nil":
                time.sleep(.5)

    #print(arr[name])
    arr[name] = list(arr[name].values())
    #print("A")
    #print(arr[name])
    return name

app.run(token = "YourNgrokToken",domain = "Create domain if you want")
#app.run(port=5972)