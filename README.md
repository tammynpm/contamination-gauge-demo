This is a mobile app 


Tech stack:
- React Native
- Expo
- FastAPI
- OpenCV
- SQLite
- Docker

Demo: 
<img src="samples/Dev/IMG_1738.PNG" alt="App Photo 1" width="240"/>
<img src="samples/Dev/IMG_1740.PNG" alt="App Photo 1" width="240"/>
<img src="samples/Dev/video.gif" alt="Demo" width="320">

System diagram:
```mermaid
flowchart LR
  A["Mobile App<br/>(React Native + Expo)"]
  C[("SQLite DB")]

  subgraph B["FastAPI Backend"]
    D["Image Analysis<br/>(OpenCV)"]
  end

  A -- "POST /analyze (image)" --> B
  A -- "GET /baselines" --> B
  A -- "GET /stats" --> B
  A -- "GET /health" --> B
  A -- "GET /ready" --> B

  B <--> C
```
