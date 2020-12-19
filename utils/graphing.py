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
    def group_by_date(data: Sequence["InstantaneousMetrics"]) -> Sequence[Sequence["InstantaneousMetrics"]]:
        """Group a sequence of InstantaneousMetrics objects by date. Pass in a sorted list only! Returns a nested list."""
        prev = None
        grouped_elements = []
        current_group = []
        for index, i in enumerate(data):
            if index == 0:
                prev = i
                current_group.append(prev)
                continue
            else:
                date = datetime.date(year=i.time.year, month=i.time.month, day=i.time.day)
                prev_date = datetime.date(year=prev.time.year, month=prev.time.month, day=prev.time.day)
                if date == prev_date:
                    current_group.append(i)
                else:
                    grouped_elements.append(current_group)
                    prev = i
                    current_group = [prev]
        return grouped_elements

    @staticmethod
    def get_day_counts(*, type_: str = "total", object_: str = None, grouped_data: Sequence[Sequence["InstantaneousMetrics"]]) -> Sequence[int]:
        """Returns a list, with counts for each day. ALL arguments must be passed as keyword arguments.
        type_ is used to specify if we need a specific channel or user counts. Defaults to `total`, in which case total message count for the day is returned.
        object_ is the ID of the object for which we need the counts"""
        map_type = {"channel": lambda i: i.get_channel_count(object_), "member": lambda j: j.get_personal_count(object_), "total": lambda k: k.total_count()}
        counts_list = [[map_type[type_](i) for i in inner_list] for inner_list in grouped_data]
        summed_days = list(map(sum, counts_list))
        return summed_days

    @staticmethod
    def get_counts_for(*, type_: str = "total", object_: str = None, time_unit: str, data: Sequence["InstantaneousMetrics"]) -> Mapping[str, Mapping]:
        """Get the individual user/channel's metrics from a given time period of InstantaneousMetrics. ALL arguments must be passed in as keyword-arguments.
         The `type` arg is used to specify which type of discord object we are looking for: channel or member. Defaults to `total`.
         The `time_unit` arg is used to specify if the graph needs times in hours, or days.
         The `object` arg refers to the specific discord.Object ID for which we need the counts. Defaults to None - this should be the case only when `type` is left as total.
         The `data` arg should be a sequence of InstantaneousMetrics objects, obtained by parsing the db response. _THIS SEQUENCE MUST BE SORTED IN ASCENDING ORDER OF DATE.__

         Usage:
            Ex: To get counts for a user, with ID 123456789, in days.
                1> Get the corresponding data from the database, and parse it into InstantaneousMetrics objects.
                2> When in the `metrics` cog, the import is `from utils import graphing`. So invoking this function will be:
                    graphing.InstantaneousMetrics.get_counts_for
                3> graphing.InstantaneousMetrics.get_counts_for(type_="member", object_=str(123456789), time_unit="days", data=sorted_and_parsed_data)
                This returns a dictionary, with the key as the object ID, and the value being another dictionary - {'x': <x axis data>, 'y': <y axis data>}.
                The object ID key in the dictionary will be None, if this function was used to get the total counts.
            Ex 2: To get total counts, in days.
                1> Get data - parse - sort
                2> graphing.InstantaneousMetrics.get_counts_for(time_unit="days", data=sorted_and_parsed_data)    -> using the default values for type_ and object_ gives the total counts.
                Again, returns a dictionary - but as mentioned above, the key will be None, the value will be a dictionary with the x and y axes data.
            Ex 3: To get counts for a channel, with ID 987654321, in hours.
                1> Get data - parse - sort
                2> graphing.InstantaneousMetrics.get_counts_for(type_="channel", object_=str(987654321), time_unit="hours", data=sorted_and_parsed_data)

        Note that this is directly returning the data for the axes.
        """
            
        channel_or_member = {"channel": lambda i: i.get_channel_count(object_), "member": lambda j: j.get_personal_count(object_), "total": lambda k: k.total_counts()}
        hours_or_days = {"hours": lambda i: i.clean_hours_repr(), "days": lambda j: j.clean_date_repr()}
        if type_ == "hours":
            x = np.array([hours_or_days[time_unit.lower()](i) for i in data])
            y = np.array([channel_or_member[type_.lower()](i) for i in data])
        else:
            # type_ is days, need to group together all data for a day, and then sum it. This is done by the group_by_date and get_day_counts functions.
            # x axis only needs one date for each day
            grouped = InstantaneousMetrics.group_by_date(data)
            x = np.array([group[0].clean_date_repr() for group in grouped])
            y = np.array(InstantaneousMetrics.get_day_counts(type_=type_, object_=object_, grouped_data=grouped))
            
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


def graph_hourly_total_message_count(data: Sequence[InstantaneousMetrics], x_axis: np.array,
                                     y_axis: [np.array], labels: [str] = None) -> ImageEmbed:

    # data for x and y axes
    x_array, y_arrays, labels = x_axis, y_axis, labels

    # prepare bytes buffer using _make_graph function
    buffer = _make_single_line_graph(f"Total messages sent today",
                                         labels=labels, xlabel="Time (hours)", ylabel="Messages", x_axis=x_array,
                                         y_axis=y_arrays)
    return make_discord_embed(buffer)

        #embed = discord.Embed(title="Metrics", description="There is no data saved for the day yet")
        #return None, embed


def _make_single_line_graph(title: str, *, labels: list, xlabel: str, ylabel: str, x_axis: np.array,
                            y_axis: [np.array]) -> io.BytesIO:
    """A general graphing function that is called by all other functions."""
    fig = Figure()
    ax = fig.subplots()

    if labels is not None:
        for i in range(len(y_axis)):
            ax.plot(x_axis, y_axis[i], label=labels[i])
    else:
        ax.plot(x_axis, y_axis[0])

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper right")

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
