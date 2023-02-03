# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from __future__ import annotations

class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        start_date : str = None,
        end_date: str = None,
        budget: str = None,
        unsupported_airports: str = None,
        geo_list: list[str] = [],
        number_list : list[str] = []
    ):
        self.destination = destination
        self.origin = origin
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget
        self.unsupported_airports = unsupported_airports
        self.geo_list = geo_list
        self.number_list = number_list
