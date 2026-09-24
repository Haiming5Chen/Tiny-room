"""Per-wheel bounded feedback, speed ramping and a simple overspeed limiter."""
from little_world.core.drive_settings import DriveSettings


class DriveAssist:
    def __init__(self):self.targets={}

    def commands(self,targets,observations,dt,settings=DriveSettings()):
        result={}
        for name,goal in targets.items():
            velocity,radius,limit,ground_speed=observations[name]
            previous=self.targets.get(name,0.)
            target=previous+max(-settings.acceleration*dt,min(settings.acceleration*dt,goal-previous))
            self.targets[name]=target
            cap=limit*settings.torque_fraction
            torque=max(-cap,min(cap,settings.gain*(target/max(.005,radius)-velocity)))
            slip=abs(velocity*radius)-abs(ground_speed)
            if settings.traction and slip>.35 and torque*velocity>0:
                torque*=max(.2,min(1.,.35/slip))
            result[name]=torque
        return result
