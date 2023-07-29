from apscheduler.schedulers.background import BackgroundScheduler
from domains_api import IPChanger, User


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(IPChanger, 'interval', minutes=10)
    scheduler.start()
