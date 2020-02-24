# zhng

𝔄𝔭𝔭𝔩𝔶 𝔞𝔩𝔩 𝔰𝔬𝔯𝔱𝔰 𝔬𝔣 𝔢𝔣𝔣𝔢𝔠𝔱𝔰 𝚝𝚘 𝚢𝚘𝚞𝚛 𝚃𝚎𝚕𝚎𝚐𝚛𝚊𝚖 𝚖𝚎𝚜𝚜𝚊𝚐𝚎𝚜 ṲϨỊИ₲ ∆И ỊИⱢỊИЄ ƁØ₮

## Usage

```
@zhngbot <your message here>
```

then select whichever effect you want.

## Development

A Dockerfile is available.

Environment variables:

- `TELEGRAM_API_TOKEN` - token for the Telegram Bot API (required)
- `RANKING_UPDATE_FREQUENCY` - frequency at which effects will be sorted based on usage frequency and stats written to disk; by default, this occurs on every update
- `POPULARITY_DATA` - location on disk where usage stats will be written; if unset, stats will not persist upon bot restart

## License

MIT