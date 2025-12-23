the valorant round clipper

moondream, a model served by ollama, looks at 1 frame/5seconds of a valorant vod and picks up the amount of time showing in the timer using the vision model.

there are criterias of how this information is used to figure out when a round starts or ends

<img width="1074" height="438" alt="image" src="https://github.com/user-attachments/assets/f9a60380-f584-4fa2-b0e1-0eb11396e6e6" />

i get these

```json
[
  {
    "timestamp": 538.7,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_538.7s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_538.7s.jpg",
    "timer_value": "spike planted"
  },
  {
    "timestamp": 548.7,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_548.7s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_548.7s.jpg",
    "timer_value": "nothing"
  },
  {
    "timestamp": 558.7,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_558.7s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_558.7s.jpg",
    "timer_value": "spike planted"
  },
  {
    "timestamp": 568.7,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_568.7s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_568.7s.jpg",
    "timer_value": "spike planted"
  },
  {
    "timestamp": 578.6,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_578.6s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_578.6s.jpg",
    "timer_value": "nothing"
  },
  {
    "timestamp": 588.6,
    "frame_path": "demo_output/match_582604/map_0/frames/frame_588.6s.jpg",
    "cropped_path": "demo_output/match_582604/map_0/cropped_timers/timer_588.6s.jpg",
    "timer_value": "nothing"
  }
]
