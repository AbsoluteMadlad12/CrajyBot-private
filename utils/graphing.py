import matplotlib
matplotlib.use("Agg")

from matplotlib.figure import Figure
import numpy as np

import datetime
import io
from typing import Sequence, Mapping, Union
from dataclasses import dataclass
from collections import namedtuple

import discord


@dataclass
class InstantaneousMetrics:
    """Represents all the data for the metrics stored for a particular datetime object."""
    time: datetime.datetime
    author_counts: dict
    channel_counts: dict
    
    def total_count(self) -> int:
        return sum(self.author_counts.values())

    def get_personal_count(self, person: str) -> int:
        # the expected ID is a string, because they're stored as strings in the database. MongoDB doesn't support integer keys.
        return self.author_counts[person]

    def get_channel_count(self, channel: str) -> int:
        return self.channel_counts[channel]

    @staticmethod
    def get_counts_for(type_: str, object_: str, time_unit: str, data: Sequence["InstantaneousMetrics"]) -> Mapping[str, Mapping]:
        # get the individual user/channel's metrics from a given time period of InstantaneousMetrics
        # the `type` arg is used to specify which type of discord object we are looking for: channel or member
        # the `time_unit` arg is used to specify if the graph needs times in hours, or days
        channel_or_member = {"channel": lambda i: i.get_channel_count(object_), "member": lambda j: j.get_personal_count(object_)}
        hours_or_days = {"hours": lambda i: i.clean_hours_repr(), "days": lambda j: j.clean_date_repr()}
        y = np.array([channel_or_member[type_.lower()](i) for i in data])
        x = np.array([hours_or_days[time_unit.lower()](i) for i in data])
        return {object_: {"x": x, "y": y}}

    def clean_hours_repr(self) -> str:
        return self.time.strftime("%H")    # returns in 00 format

    def clean_date_repr(self) -> str:
        return self.time.strftime("%d/%m/")


ImageEmbed = namedtuple("ImageEmbed", "file embed")

def parse_data(db_response: dict) -> InstantaneousMetrics:
    """Convert the mongodb response dictionary into the dataclass instance.
    The dictionary is in the form `{datetime: <time inserted>, author_counts: <dict containing message count for each user>, channel_counts: >dict containing message counts for each channel>}`."""
    return InstantaneousMetrics(time=db_response["datetime"], author_counts=db_response["author_counts"], channel_counts=db_response["channel_counts"])


def graph_hourly_message_count(data: Sequence[InstantaneousMetrics]) -> ImageEmbed:
    # data for x and y axes
    x_array = np.array([x.clean_hours_repr() for x in data])
    y_array = np.array([y.total_count() for y in data])
    # prepare bytes buffer using _make_graph function
    buffer = _make_single_line_graph(f"Total messages sent, hourly\n{data[0].time.year}/{data[0].time.month}/{data[0].time.day}", xlabel="Time", ylabel="Messages", x_axis=x_array, y_axis=y_array)
    return make_discord_embed(buffer)


def _make_single_line_graph(title: str, *, xlabel: str, ylabel: str, x_axis: np.array, y_axis: np.array) -> io.BytesIO:
    """A general graphing function that is called by all other functions."""
    fig = Figure()
    ax = fig.subplots()

    ax.plot(x_axis, y_axis)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # a bytes buffer to which the generated graph image will be stored, instead of saving every graph image.
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inchex="tight")     # saves file with name <date>-<first plotted hour>-<last plotted hour>
    buffer.seek(0)

    return buffer


def _make_multi_line_graph() -> io.BytesIO:
    # implement similar to single_line_graph
    pass


def make_discord_embed(image_buffer: io.BytesIO) -> ImageEmbed:
    """Converts the BytesIO buffer into a discord.File object that can be sent to any channel."""
    file_for_discord = discord.File(fp=image_buffer, filename="buffer.png")
    embed = discord.Embed()
    embed.set_image(url="attachment://buffer.png")
    return ImageEmbed(file_for_discord, embed)
