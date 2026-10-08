# Fetch: the table camera off its believed pose

The arm on a cart as designed, the Fetch program solved for it, the table camera set off where the program believes it (ADR 0039): shifted along the field's axes, or panned (about its up axis) or tilted (about its right axis). "Predicted" is where the closed form puts the cube the program sees, from the true cube; "seen" is where its last look saw it, against where the cube really was.

| Camera off by | Predicted aim error (X / Y / Z, mm) | Seen off the cube (X / Y / Z, mm) | Fetched | What happened |
| --- | --- | --- | --- | --- |
| X -30 mm | +30.0 / +0.0 / +0.0 | +31.1 / -0.0 / -0.5 | **no** | the reach down was stopped, it looked again, and was stopped again |
| X -20 mm | +20.0 / +0.0 / +0.0 | +22.1 / -0.1 / -0.4 | **no** | the reach down was stopped, it looked again, and was stopped again |
| X -15 mm | +15.0 / +0.0 / +0.0 | +17.1 / +0.0 / -0.5 | **no** | lifted, then dropped on the way to the bin |
| X -12.5 mm | +12.5 / +0.0 / +0.0 | +14.8 / +0.0 / -0.5 | **no** | lifted, then dropped on the way to the bin |
| X -10 mm | +10.0 / +0.0 / +0.0 | +10.5 / +0.0 / -0.4 | yes |  |
| X -5 mm | +5.0 / +0.0 / +0.0 | +6.2 / +0.0 / -0.5 | yes |  |
| X -2.5 mm | +2.5 / +0.0 / +0.0 | +3.4 / +0.0 / -0.5 | yes |  |
| X +2.5 mm | -2.5 / +0.0 / +0.0 | -1.3 / +0.3 / -0.5 | yes |  |
| X +5 mm | -5.0 / +0.0 / +0.0 | -3.7 / +0.0 / -0.4 | yes |  |
| X +10 mm | -10.0 / +0.0 / +0.0 | -8.3 / +0.0 / -0.4 | yes |  |
| X +15 mm | -15.0 / +0.0 / +0.0 | -13.1 / +0.0 / -0.4 | yes |  |
| X +20 mm | -20.0 / +0.0 / +0.0 | -18.0 / +0.0 / -0.4 | yes |  |
| X +30 mm | -30.0 / +0.0 / +0.0 | -27.8 / -0.0 / -0.3 | yes |  |
| Y -30 mm | +0.0 / +30.0 / +0.0 | +1.4 / +30.1 / -0.5 | **no** | the reach down was stopped, it looked again, and was stopped again |
| Y -25 mm | +0.0 / +25.0 / +0.0 | +1.1 / +24.9 / -0.5 | yes |  |
| Y -20 mm | +0.0 / +20.0 / +0.0 | +1.1 / +20.2 / -0.6 | yes |  |
| Y -15 mm | +0.0 / +15.0 / +0.0 | +1.1 / +14.4 / -0.5 | yes |  |
| Y -10 mm | +0.0 / +10.0 / +0.0 | +1.1 / +10.6 / -0.6 | yes |  |
| Y -5 mm | +0.0 / +5.0 / +0.0 | +0.9 / +4.8 / -0.6 | yes |  |
| Y -2.5 mm | +0.0 / +2.5 / +0.0 | +0.9 / +2.9 / -0.5 | yes |  |
| Y +2.5 mm | +0.0 / -2.5 / +0.0 | +1.1 / -2.9 / -0.5 | yes |  |
| Y +5 mm | +0.0 / -5.0 / +0.0 | +1.2 / -4.8 / -0.5 | yes |  |
| Y +10 mm | +0.0 / -10.0 / +0.0 | +1.1 / -10.6 / -0.4 | yes |  |
| Y +15 mm | +0.0 / -15.0 / +0.0 | +1.2 / -14.4 / -0.4 | yes |  |
| Y +20 mm | +0.0 / -20.0 / +0.0 | +1.2 / -20.2 / -0.5 | yes |  |
| Y +25 mm | +0.0 / -25.0 / +0.0 | +1.1 / -24.9 / -0.5 | yes |  |
| Y +30 mm | +0.0 / -30.0 / +0.0 | +1.3 / -29.9 / -0.6 | **no** | the reach down was stopped, it looked again, and was stopped again |
| Z -30 mm | +0.0 / +0.0 / +30.0 | +1.5 / +0.0 / +29.4 | yes |  |
| Z -20 mm | +0.0 / +0.0 / +20.0 | +2.0 / +0.0 / +19.5 | yes |  |
| Z -15 mm | +0.0 / +0.0 / +15.0 | +1.2 / +0.0 / +14.4 | yes |  |
| Z -10 mm | +0.0 / +0.0 / +10.0 | +2.6 / +0.0 / +9.5 | yes |  |
| Z -5 mm | +0.0 / +0.0 / +5.0 | +1.8 / +0.0 / +4.5 | yes |  |
| Z -2.5 mm | +0.0 / +0.0 / +2.5 | +2.6 / +0.0 / +2.0 | yes |  |
| Z +2.5 mm | +0.0 / +0.0 / -2.5 | +1.8 / +0.2 / -3.0 | yes |  |
| Z +5 mm | +0.0 / +0.0 / -5.0 | +2.2 / +0.0 / -5.4 | yes |  |
| Z +10 mm | +0.0 / +0.0 / -10.0 | +2.0 / +0.0 / -10.3 | yes |  |
| Z +12.5 mm | +0.0 / +0.0 / -12.5 | +2.5 / -0.0 / -12.8 | **no** | carried to the bin, but never lifted the 5 cm the goal asks |
| Z +15 mm | +0.0 / +0.0 / -15.0 | +1.2 / +0.0 / -15.4 | **no** | carried to the bin, but never lifted the 5 cm the goal asks |
| Z +20 mm | +0.0 / +0.0 / -20.0 | +2.2 / +0.0 / -20.6 | **no** | the reach down was stopped, it looked again, and was stopped again |
| Z +30 mm | +0.0 / +0.0 / -30.0 | +1.3 / +0.0 / -30.7 | **no** | the reach down was stopped, it looked again, and was stopped again |
| pan -3 deg | +0.6 / -45.8 / +1.0 | +2.6 / -45.9 / +0.6 | **no** | the reach down was stopped, it looked again, and was stopped again |
| pan -2 deg | +0.3 / -30.6 / +0.5 | +2.0 / -30.2 / -0.1 | **no** | the reach down was stopped, it looked again, and was stopped again |
| pan -1.75 deg | +0.2 / -26.7 / +0.4 | +1.4 / -26.4 / -0.1 | yes |  |
| pan -1.5 deg | +0.2 / -22.9 / +0.3 | +1.3 / -22.5 / -0.2 | yes |  |
| pan -1 deg | +0.1 / -15.3 / +0.1 | +1.2 / -14.7 / -0.4 | yes |  |
| pan -0.5 deg | +0.0 / -7.6 / +0.0 | +0.9 / -6.9 / -0.5 | yes |  |
| pan -0.25 deg | +0.0 / -3.8 / +0.0 | +1.1 / -3.0 / -0.4 | yes |  |
| pan +0.25 deg | +0.0 / +3.8 / +0.0 | +1.0 / +3.0 / -0.6 | yes |  |
| pan +0.5 deg | +0.0 / +7.6 / +0.0 | +0.8 / +6.9 / -0.6 | yes |  |
| pan +1 deg | +0.1 / +15.3 / +0.1 | +1.1 / +14.7 / -0.5 | yes |  |
| pan +1.5 deg | +0.2 / +22.9 / +0.3 | +1.2 / +22.5 / -0.3 | yes |  |
| pan +1.75 deg | +0.2 / +26.7 / +0.4 | +1.3 / +26.4 / -0.1 | yes |  |
| pan +2 deg | +0.3 / +30.6 / +0.5 | +2.0 / +30.2 / +0.0 | **no** | the reach down was stopped, it looked again, and was stopped again |
| pan +3 deg | +0.6 / +45.8 / +1.0 | +2.4 / +45.8 / +0.6 | **no** | the reach down was stopped, it looked again, and was stopped again |
| tilt -3 deg | -38.6 / +0.0 / +24.8 | -38.2 / +0.0 / +24.7 | yes |  |
| tilt -2 deg | -25.9 / +0.0 / +16.3 | -24.6 / -0.0 / +16.0 | yes |  |
| tilt -1.5 deg | -19.5 / +0.0 / +12.1 | -17.8 / -0.0 / +11.7 | yes |  |
| tilt -1 deg | -13.0 / +0.0 / +8.0 | -10.7 / +0.0 / +7.6 | yes |  |
| tilt -0.5 deg | -6.5 / +0.0 / +4.0 | -5.6 / +0.0 / +3.5 | yes |  |
| tilt -0.25 deg | -3.3 / +0.0 / +2.0 | -2.5 / +0.0 / +1.5 | yes |  |
| tilt +0.25 deg | +3.3 / +0.0 / -2.0 | +4.6 / +0.0 / -2.5 | yes |  |
| tilt +0.5 deg | +6.6 / +0.0 / -3.9 | +8.1 / +0.3 / -4.4 | yes |  |
| tilt +0.75 deg | +9.8 / +0.0 / -5.9 | +11.6 / +0.0 / -6.4 | yes |  |
| tilt +1 deg | +13.1 / +0.0 / -7.8 | +15.2 / +0.0 / -8.3 | **no** | lifted under 5 cm, then dropped on the way |
| tilt +1.5 deg | +19.8 / +0.0 / -11.6 | +22.0 / +0.0 / -12.2 | **no** | lifted under 5 cm, then dropped on the way |
| tilt +2 deg | +26.4 / +0.0 / -15.4 | +28.6 / -0.0 / -15.3 | **no** | the reach down was stopped, it looked again, and was stopped again |
| tilt +3 deg | +39.8 / +0.0 / -22.7 | +41.5 / -0.0 / -22.3 | **no** | the reach down was stopped, it looked again, and was stopped again |

## 59 drawn set-ups

The same 60 set-ups each time - the design as designed and 59 drawn at random within the ranges of ADR 0024 - with the camera off by one error. The rate is over the drawn set-ups (ADR 0028).

| Camera off by | Every goal met | Drawn at random | Missed in |
| --- | --- | --- | --- |
| pan +1.5 deg | 60 of 60 | 59 of 59, at least 95 % | - |
| tilt +0.5 deg | 60 of 60 | 59 of 59, at least 95 % | - |
| X -10 mm | 59 of 60 | 58 of 59, at least 92 % | repeat 46 |
| Z +10 mm | 60 of 60 | 59 of 59, at least 95 % | - |
| tilt +1 deg | 8 of 60 | 8 of 59, at least 7 % | 52 set-ups |
