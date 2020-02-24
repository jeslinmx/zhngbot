import json
import logging
import os
import time
from collections import defaultdict

from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.ext import (
    CallbackContext,
    ChosenInlineResultHandler,
    InlineQueryHandler,
    Updater,
)
from telegram.ext.dispatcher import run_async

from transforms import transforms as tfs

# configure from environment variables
api_token = os.getenv("TELEGRAM_API_TOKEN")
ranking_update_frequency = int(os.getenv("RANKING_UPDATE_FREQUENCY", "0"))
popularity_filename = os.path.join(os.getenv("POPULARITY_DATA"), "popularity.json")

# initialize globals
# tracks number of uses of each transform
popularity = {
    "global": {tf_name: 0 for tf_name in tfs}
}
# stores the order in which transforms are presented, periodically
# updated to favour the most commonly used transforms
ranking = defaultdict(lambda: list(tfs.keys()))

@run_async
def process_query(upd: Update, ctx: CallbackContext):
    if upd.inline_query.query:
        upd.inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id=tf_name,
                    title=tfs[tf_name](upd.inline_query.query),
                    input_message_content=InputTextMessageContent(
                        message_text=tfs[tf_name](upd.inline_query.query),
                    ),
                    description=f"{tf_name}",
                )
                for tf_name in ranking.get(str(upd.effective_user.id), ranking["global"])
            ],
            cache_time=0,
        )

def count_hits(upd: Update, ctx: CallbackContext):
    if str(upd.effective_user.id) not in popularity:
        popularity[str(upd.effective_user.id)] = {tf_name: 0 for tf_name in tfs}
    popularity["global"][upd.chosen_inline_result.result_id] += 1
    popularity[str(upd.effective_user.id)][upd.chosen_inline_result.result_id] += 1

    # if RANKING_UPDATE_FREQUENCY is 0, update rankings every time the API
    # sends inline query feedback
    if not ranking_update_frequency:
        update_ranking(ctx)

@run_async
def update_ranking(ctx: CallbackContext):
    # sort all rankings based on each user's use-count, falling back to global
    # use-count as a tiebreaker
    for user_id in popularity:
        ranking[user_id].sort(
            key=lambda tf_name: (
                popularity[user_id][tf_name],
                popularity["global"][tf_name]
            ),
            reverse=True,
        )
    # write current popularity numbers to disk
    if popularity_filename:
        with open(popularity_filename, "w") as popularity_data:
            json.dump(popularity, popularity_data)
        logging.info(f"popularity numbers written to {popularity_filename} at {time.asctime()}")

@run_async
def handle_error(upd: Update, ctx: CallbackContext):
    raise

def main():
    global popularity
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
        level=logging.INFO,
    )

    # load popularity numbers from disk
    if popularity_filename:
        try:
            with open(popularity_filename, "r") as popularity_data:
                popularity = json.load(popularity_data)
            logging.info(f"popularity numbers loaded from {popularity_filename}.")
        except FileNotFoundError:
            logging.warning(f"popularity data could not be found at {popularity_filename}; counting from scratch.")
    else:
        logging.warning("POPULARITY_DATA not set, popularity will not be saved for this session.")

    u = Updater(token=api_token, use_context=True)

    d = u.dispatcher
    d.add_handler(InlineQueryHandler(
        callback=process_query,
    ))
    d.add_handler(ChosenInlineResultHandler(
        callback=count_hits,
    ))
    d.add_error_handler(handle_error)

    j = u.job_queue
    if ranking_update_frequency:
        j.run_repeating(update_ranking, ranking_update_frequency)
    else:
        update_ranking(None) # guarantees update_ranking runs on startup

    u.start_polling()
    u.idle()

if __name__ == "__main__":
    main()