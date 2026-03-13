from threading import Timer

import pytz
import structlog

from deskflow import context
from deskflow.conversation import Conversation
from deskflow.stage.bot_stage import AskStartMenuStage

log = structlog.get_logger()

TZ = pytz.timezone("America/Sao_Paulo")
UTC = pytz.UTC
INACTIVITY_TIMER_INTERVAL = 30  # every minute


class RepeatTimer(Timer):
    def __init__(self, interval, function, args=None, kwargs=None):
        Timer.__init__(self, interval, function, args, kwargs)
        self.daemon = True

    def run(self):
        while not self.finished.wait(self.interval):
            try:
                self.function(*self.args, **self.kwargs)
            except:  # noqa E722
                log.exception("Timer function error")


def start():
    RepeatTimer(INACTIVITY_TIMER_INTERVAL, on_inactivity_timer).start()
    pass


def on_inactivity_timer():
    inactivities = context.get_inactive()

    for ctx in inactivities:
        replies = AskStartMenuStage().handle_input(msisdn=ctx.msisdn, text="")
        c = Conversation(msisdn=ctx.msisdn, ctx=ctx, data={})

        for reply in replies:
            request_suggestion_sent = ctx.data.get(
                "request_suggestion_sent", False
            )
            if not request_suggestion_sent:
                c.reply(reply=reply)
                context.merge(
                    msisdn=ctx.msisdn, data={"request_suggestion_sent": True}
                )
