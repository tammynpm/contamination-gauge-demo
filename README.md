I built a mobile application with a backend pipeline that processes user-provided inputs to detect contamination for a job application. But they found the developer before I could turn my resume in lol. This project focused on designing the system to handle untrusted input and explored how it behaves under malformed and adversarial input. 

Tech stack:
- React Native
- Expo
- FastAPI
- OpenCV
- SQLite
- Docker

Testing method:
- send correupted data & unexpected payloads

Demo: 
<img src="samples/Dev/IMG_1738.PNG" alt="App Photo 1" width="240"/>
<img src="samples/Dev/IMG_1740.PNG" alt="App Photo 1" width="240"/>
<!-- <img src="samples/Dev/video.gif" alt="Demo" width="320"> -->

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
