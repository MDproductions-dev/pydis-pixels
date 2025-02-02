import io
import time
import datetime

import discord.ext.commands
import discord.http
import PIL.Image


__version__ = '2.2.0'


EMBED_TITLE = 'Pixels State'
EMBED_FOOTER = 'Last updated'
IMAGE_SCALE = 5
GITHUB_REPO_URL = 'https://github.com/JMcB17/pydis-pixels'
GITHUB_PAGE_URL = 'https://jmcb17.github.io/pydis-pixels/pages/'
DISCORD_SERVER_URL = 'discord.gg/python'


class MirrorBot(discord.ext.commands.Bot):
    def __init__(self, channel_id: int, message_id: int, canvas_size: dict, *args, **kwargs):
        super().__init__(command_prefix='pixels.', help_command=None, *args, **kwargs)
        self.channel_id = channel_id
        self.message_id = message_id
        self.canvas_size = canvas_size

        for command in [startmirror, repo, compendium, python_discord]:
            # noinspection PyTypeChecker
            self.add_command(command)

    async def create_canvas_mirror(self, discord_channel: discord.TextChannel) -> discord.Message:
        embed = discord.Embed(title=EMBED_TITLE)
        embed.set_footer(text=EMBED_FOOTER)
        mirror_message = await discord_channel.send(embed=embed)

        self.channel_id = mirror_message.channel.id
        self.message_id = mirror_message.id

        return mirror_message

    # noinspection PyProtectedMember
    async def update_canvas_mirror(self, canvas_bytes: bytes, discord_message: discord.Message):
        # todo: redo this with official methods when new discord.py version releases
        file_name = f'pixels_mirror_{time.time()}.png'
        embed = discord_message.embeds[0]
        embed.set_image(url=f'attachment://{file_name}')
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        embed_dict = embed.to_dict()
        payload_dict = {
            'embed': embed_dict,
            # get rid of the previous attachments
            'attachments': []
        }

        canvas_pil = PIL.Image.frombytes(
            'RGB',
            (self.canvas_size['width'], self.canvas_size['height']),
            canvas_bytes)
        canvas_pil = canvas_pil.resize(
            (self.canvas_size['width'] * IMAGE_SCALE, self.canvas_size['height'] * IMAGE_SCALE),
            resample=PIL.Image.NEAREST
        )
        with io.BytesIO() as byte_stream:
            canvas_pil.save(byte_stream, format='PNG')
            byte_stream.seek(0)
            canvas_discord_file = discord.File(byte_stream, filename=file_name)
            discord_file_json = {
                'name': 'file',
                'value': canvas_discord_file.fp,
                'filename': canvas_discord_file.filename,
                'content_type': 'application/octet-stream'
            }

            form = [
                {
                    'name': 'payload_json',
                    'value': discord.utils.to_json(payload_dict),
                },
                discord_file_json
            ]

            route = discord.http.Route(
                'PATCH', '/channels/{channel_id}/messages/{message_id}',
                channel_id=discord_message.channel.id, message_id=discord_message.id
            )
            data = await discord_message._state.http.request(
                route, files=[canvas_discord_file], form=form,
            )
            discord_message._update(data)
            canvas_discord_file.close()

    async def update_mirror_from_id(self, canvas_bytes: bytes):
        if not self.channel_id or not self.message_id:
            return

        channel = self.get_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)
        await self.update_canvas_mirror(canvas_bytes, message)


@discord.ext.commands.command()
@discord.ext.commands.is_owner()
async def startmirror(ctx: discord.ext.commands.Context, channel: discord.TextChannel):
    message = await ctx.bot.create_canvas_mirror(channel)
    await ctx.send(f'Done, message ID: {message.id}, channel ID: {channel.id}')


@discord.ext.commands.command(aliases=['github', 'source'])
async def repo(ctx: discord.ext.commands.Context):
    return await ctx.send(GITHUB_REPO_URL)


@discord.ext.commands.command()
async def compendium(ctx: discord.ext.commands.Context):
    return await ctx.send(f'<{GITHUB_PAGE_URL}>')


@discord.ext.commands.command(aliases=['discord', 'pydis'])
async def python_discord(ctx: discord.ext.commands.Context):
    return await ctx.send(DISCORD_SERVER_URL)
