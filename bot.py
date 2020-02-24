import json
import logging
import os
import time

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

from transforms import transforms

# configure from environment variables
api_token = os.getenv("TELEGRAM_API_TOKEN")
ranking_update_frequency = int(os.getenv("RANKING_UPDATE_FREQUENCY", "0"))
popularity_filename = os.getenv("POPULARITY_DATA")

# initialize globals
popularity = {transform_name: 0 for transform_name in transforms}
ranking = list(transforms.keys())

@run_async
def process_query(upd: Update, ctx: CallbackContext):
    if upd.inline_query.query:
        upd.inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id=name,
                    title=transforms[name](upd.inline_query.query),
                    input_message_content=InputTextMessageContent(
                        message_text=transforms[name](upd.inline_query.query),
                    ),
                    description=f"{name}",
                )
                for name in ranking
            ],
            cache_time=0,
        )

def count_hits(upd: Update, ctx: CallbackContext):
    popularity[upd.chosen_inline_result.result_id] += 1
    # if RANKING_UPDATE_FREQUENCY is default (0), update every time the API
    # sends inline query feedback
    if not ranking_update_frequency:
        update_ranking(ctx)

@run_async
def update_ranking(ctx: CallbackContext):
    # revise the order in which the transforms are presented to latest numbers
    ranking.sort(
        key=lambda key: popularity[key],
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
            update_ranking(None)
        except FileNotFoundError:
            logging.warning(f"popularity data could not be found at {popularity_filename}; counting from scratch.")
    else:
        logging.info("POPULARITY_DATA not set, popularity will not be saved for this session.")

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

    u.start_polling()
    u.idle()

if __name__ == "__main__":
    main()