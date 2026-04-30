from src.services.follow_up import FollowUp
from apscheduler.schedulers.blocking import BlockingScheduler

def main():
    schedular = BlockingScheduler()
    follow_up = FollowUp()
    follow_up.workflow()
    schedular.add_job(follow_up.workflow, "interval", minutes=1)

    schedular.start()

if __name__ == "__main__":
    main()