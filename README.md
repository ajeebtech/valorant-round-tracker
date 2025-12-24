the valorant round clipper

moondream, a model served by ollama, looks at 1 frame/5seconds of a valorant vod and picks up the amount of time showing in the timer using the vision model.

there are criterias of how this information is used to figure out when a round starts or ends:

<img width="1142" height="511" alt="image" src="https://github.com/user-attachments/assets/d2cffd02-dcf3-416a-a6bd-8fbdcc95c855" />



so when moondream finds a cropped frame of the timer space, it describes the frame and then we make sense of that, is it a timer value, is it a spike, or is it just nothing(running ads, breaks, replays, technical pause)

<img width="400" height="200" alt="image" src="https://github.com/user-attachments/assets/79e0c8ac-3b15-4543-83c0-522e0e674508" />


```json
[
  {
    "round_number": 1,
    "start_timestamp": 17.0,
    "start_time_fmt": "0:17",
    "observed_start_timestamp": 20.0,
    "start_timer": "1:37",
    "end_timestamp": 120.0,
    "end_time_fmt": "2:00",
    "end_reason": "timer_disappeared",
    "spike_planted": true,
    "spike_plant_timestamp": 80.0,
    "duration": 103.0
  },
  {
    "round_number": 2,
    "start_timestamp": 150.0,
    "start_time_fmt": "2:30",
    "observed_start_timestamp": 160.0,
    "start_timer": "1:30",
    "end_timestamp": 270.0,
    "end_time_fmt": "4:30",
    "end_reason": "timer_disappeared",
    "spike_planted": true,
    "spike_plant_timestamp": 230.0,
    "duration": 120.0
  },
  {
    "round_number": 3,
    "start_timestamp": 306.0,
    "start_time_fmt": "5:06",
    "observed_start_timestamp": 310.0,
    "start_timer": "1:36",
    "end_timestamp": 390.0,
    "end_time_fmt": "6:30",
    "end_reason": "timer_disappeared",
    "spike_planted": true,
    "spike_plant_timestamp": 380.0,
    "duration": 84.0
  },
  {
    "round_number": 4,
    "start_timestamp": 488.0,
    "start_time_fmt": "8:08",
    "observed_start_timestamp": 490.0,
    "start_timer": "1:38",
    "end_timestamp": 530.0,
    "end_time_fmt": "8:50",
    "end_reason": "timer_disappeared",
    "spike_planted": false,
    "spike_plant_timestamp": null,
    "duration": 42.0
  },
  {
    "round_number": 5,
    "start_timestamp": 556.0,
    "start_time_fmt": "9:16",
    "observed_start_timestamp": 560.0,
    "start_timer": "1:36",
    "end_timestamp": 670.0,
    "end_time_fmt": "11:10",
    "end_reason": "timer_disappeared",
    "spike_planted": false,
    "spike_plant_timestamp": null,
    "duration": 114.0
  },
  {
    "round_number": 6,
    "start_timestamp": 693.0,
    "start_time_fmt": "11:33",
    "observed_start_timestamp": 700.0,
    "start_timer": "1:33",
    "end_timestamp": 800.0,
    "end_time_fmt": "13:20",
    "end_reason": "timer_disappeared",
    "spike_planted": true,
    "spike_plant_timestamp": 760.0,
    "duration": 107.0
  },
  {
    "round_number": 7,
    "start_timestamp": 881.0,
    "start_time_fmt": "14:41",
    "observed_start_timestamp": 890.0,
    "start_timer": "1:31",
    "end_timestamp": 930.0,
    "end_time_fmt": "15:30",
    "end_reason": "timer_disappeared",
    "spike_planted": false,
    "spike_plant_timestamp": null,
    "duration": 49.0
  },
  {
    "round_number": 8,
    "start_timestamp": 971.0,
    "start_time_fmt": "16:11",
    "observed_start_timestamp": 980.0,
    "start_timer": "1:31",
    "end_timestamp": 1060.0,
    "end_time_fmt": "17:40",
    "end_reason": "timer_disappeared",
    "spike_planted": false,
    "spike_plant_timestamp": null,
    "duration": 89.0
  },
  {
