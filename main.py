import traceback
from subs2graph.consts import DEBUG
from subs2graph.utils import send_email
from subs2graph.videos_sn_creator import get_best_directors

if __name__ == "__main__":
    try:
        get_best_directors()

    except Exception as e:
        if not DEBUG:
            send_email("dimakagan15@gmail.com", "Subs2Graph Code Crashed & Exited", traceback.format_exc())
        else:
            raise e
    if not DEBUG:
        send_email("dimakagan15@gmail.com", "Subs2Graph Code Finished", "Code Finished")
