from dataclasses import dataclass, field

import pandas as pd
from rich.table import Table

from .record import Record


@dataclass
class Stats:
    """Store result of all tokenized data"""

    name: str = ""
    records: list[Record] = field(default_factory=lambda: [])

    @property
    def total(self):
        """Return the number of total records"""
        return len(self.records)

    @property
    def correct(self):
        """Return the number of correct records"""
        return [r.is_correct for r in self.records].count(True)

    @property
    def exactness(self):
        """Return the number of exact records"""
        return [r.is_exact for r in self.records].count(True)

    @property
    def correct_rate(self):
        """Return the correct rate"""
        return self.correct / self.total

    @property
    def exact_rate(self):
        """Return the exact rate"""
        return self.exactness / self.total

    @property
    def dirty(self):
        """Return the number of records that contains '?'"""
        return sum([r.dirty for r in self.records])

    @property
    def simple(self):
        return {
            "name": self.name,
            "exact": self.exactness,
            "correct": self.correct,
            "total": self.total,
            "exact_rate": self.exact_rate,
            "correct_rate": self.correct_rate,
            "dirty": self.dirty,
        }

    @staticmethod
    def sum(stats: list["Stats"], name: str = "total"):
        """Return the sum of stats"""
        return Stats(name, [r for s in stats for r in s.records])

    @staticmethod
    def dataframe(stats: list["Stats"], total=None):
        """Return the dataframe of stats"""
        if total is None:
            total = Stats.sum(stats)
        return pd.DataFrame([s.simple for s in stats] + [total.simple])

    @staticmethod
    def table(stats: list["Stats"], total=None, title: str = "Result", show_footer: bool = True):
        """Return the table of stats"""
        table = Table(title=title, show_footer=show_footer)
        if total is None:
            total = Stats.sum(stats)
        total = total.simple
        table.add_column("File", footer="Total", justify="center")
        table.add_column("Exact", footer=str(total["exact"]), justify="center")
        table.add_column("Correct", footer=str(total["correct"]), justify="center")
        table.add_column("Total", footer=str(total["total"]), justify="center")
        table.add_column(
            "Exact Rate", footer=f"{round(total['exact_rate'] * 100, 2)}%", justify="center"
        )
        table.add_column(
            "Correct Rate", footer=f"{round(total['correct_rate'] * 100, 2)}%", justify="center"
        )
        table.add_column("Dirty", footer=str(total["dirty"]), justify="center")
        for s in stats:
            table.add_row(
                s.simple["name"],
                str(s.simple["exact"]),
                str(s.simple["correct"]),
                str(s.simple["total"]),
                f"{round(s.simple['exact_rate'] * 100, 2)}%",
                f"{round(s.simple['correct_rate'] * 100, 2)}%",
                str(s.simple["dirty"]),
            )
        return table
