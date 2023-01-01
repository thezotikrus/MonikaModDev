default persistent._mas_current_consumable = {
    0: {
        "prep_time": None,
        "consume_time": None,
        "id": None,
    },
    1: {
        "prep_time": None,
        "consume_time": None,
        "id": None
    }
}

#Dict of dicts:
#{
#   "consumable_id": {
#       "enabled": True/False,
#       "times_had": int,
#       "servings_left": int
#   },
#   ...
#}
default persistent._mas_consumable_map = dict()

init python in mas_consumables:
    #Consumable types for sorting in the consumable map
    TYPE_DRINK = 0
    TYPE_FOOD = 1

    #Consumable prop constants
    #We'll store some shorthand constants for ways to route/say dialogue for consumables here
    CONTAINER_NONE = None
    CONTAINER_PLATE = "plate"
    CONTAINER_CUP = "cup"
    AMOUNT_SOME = "some"

    #Property names
    # key: marks the string to use when referencing the object's container
    # value: string - container name
    PROP_CONTAINER_REF = "container"
    # key: marks the reference for the object
    # value: string - reference name to use (slice, batch, etc.) (Used if no container found)
    PROP_OBJ_REF = "obj_ref"
    # key: marks the reference for certain amount of the object
    # value: string (e.g. 'some' or 'a few')
    PROP_AMOUNT_REF = "amount_ref"
    # key: marks whether the consumable should be referred to in plural or not
    # value: boolean, True if plural, False if not.
    PROP_PLUR = "plural"
    # key: marks whether Monika can take this consumable with her when going out or not
    # value: boolean, True if can, False if not (not specified == False)
    # TODO: Right now ONLY for drinks, containers for food wen?
    PROP_PORTABLE = "portable"
    # key: marks whether this consumable is compatible with consumables of the opposite type (food w/ drink or drink w/ food)
    # value: boolean, True if is compatible, False if not (not specified == False)
    # TODO: allow value to be a const, so if a drink and food has the same value, they are compatible
    PROP_COMPATIBLE = "compatible"

    #Some templates for consumables
    PREP_HOT_DRINK = {
        PROP_CONTAINER_REF: CONTAINER_CUP,
        PROP_AMOUNT_REF: AMOUNT_SOME,
        PROP_PLUR: False,
        PROP_PORTABLE: True,
        PROP_COMPATIBLE: True
    }

    NON_PREP_PASTRY = {
        PROP_CONTAINER_REF: CONTAINER_NONE,
        PROP_PLUR: False,
        PROP_COMPATIBLE: True
    }

    NON_PREP_CAKE = {
        PROP_CONTAINER_REF: CONTAINER_PLATE,
        PROP_AMOUNT_REF: AMOUNT_SOME,
        PROP_OBJ_REF: "slice",
        PROP_PLUR: False,
        PROP_COMPATIBLE: True
    }

    # Keys for acs map for consumables
    # NOTE: An acs map for a consomable MUST always have an acs (and hence the key) for the full state,
    # as it can be used as a fallback for the missing acs
    CONS_FULL = "full"
    CONS_HALFDONE = "half-done"
    CONS_DONE = "done"

    #Dict of dicts:
    #consumable_map = {
    #   0: {"consumable_id": MASConsumable},
    #   1: {"consumable_id": MASConsumable}
    #}
    consumable_map = dict()

#NOTE: For consumables, to make things both consistent and easier to deal with, the following rules should be applied to the acs:
#1. Drinks always go on Monika's right
#2. Foods always go on Monika's left

init 5 python:
    import random
    #MASConsumable class
    class MASConsumable(object):
        """
        Consumable class

        PROPERTIES:
            consumable_id - id of the consumable
            consumable_type - Type of consumable this is
            disp_name - friendly name for this consumable
            ex_props - additional properties for describing this consumable
            start_end_tuple_list - list of (start_hour, end_hour) tuples
            acs_map - map of MASAccessory objects to display for the consumable
            split_list - list of split hours
            should_restock_warn - whether or not Monika should warn the player that she's running out of this consumable
            late_entry_list - list of integers storing the hour which would be considered a late entry
            max_re_serve - amount of times Monika can get a re-serving of this consumable
            max_stock_amount - maximum stock amount of this consumable to hold
            cons_chance - likelihood of Monika to keep having this consumable
            prep_low - bottom bracket of preparation time (NOTE: Should be passed in as number of seconds)
            prep_high - top bracket of preparation time (NOTE: Should be passed in as number of seconds)
            cons_low - bottom bracket of consumable time (NOTE: Should be passed in as number of seconds)
            cons_high - top bracket of consumable time (NOTE: Should be passed in as number of seconds)
            done_cons_until - the time until Monika can randomly have this consumable again
            get_cons_evl - evl to use for getting the consumable (no prep)
            finish_prep_evl - evl to use when finished preparing a consumable
            finish_cons_evl - evl to use when finished having a consumable
        """

        #Constants:
        #Drink prep/finish drink/get drink eventlabels
        BREW_FINISH_EVL = "mas_finished_brewing"
        DRINK_FINISH_EVL = "mas_finished_drinking"
        DRINK_GET_EVL = "mas_get_drink"

        #Food prep/finish eat/get food eventlabels
        PREP_FINISH_EVL = "mas_finished_prepping"
        FOOD_FINISH_EVL = "mas_finished_eating"
        FOOD_GET_EVL = "mas_get_food"

        DEF_DONE_CONS_TD = datetime.timedelta(hours=2)

        LOW_STOCK_AMT = 10
        LOW_CRITICAL_STOCK_AMT = 1

        def __init__(
            self,
            consumable_id,
            consumable_type,
            disp_name,
            start_end_tuple_list,
            acs_map,
            split_list=None,
            ex_props=None,
            should_restock_warn=True,
            late_entry_list=None,
            max_re_serve=None,
            max_stock_amount=150,
            cons_chance=80,
            cons_low=10*60,
            cons_high=2*3600,
            prep_low=2*60,
            prep_high=4*60,
            get_cons_evl=None,
            finish_prep_evl=None,
            finish_cons_evl=None
        ):
            """
            MASConsumable constructor

            IN:
                consumable_id - id for the consumable
                    NOTE: Must be unique

                consumable_type - type of consumable:
                    0 - Drink
                    1 - Food

                disp_name - Friendly diaply name (for use in dialogue)

                start_end_tuple_list - list of tuples storing (start_hour, end_hour)
                    NOTE: Does NOT support midnight crossover times. If needed, requires a separate entry
                    NOTE: end_hour is exclusive

                acs_map - map of MASAccessory objects for this consumable (for 'full' (0%-65%), 'half-done' (66%-90%), and 'done' (91%-100%) states).
                    The 'full' key must always be present.

                split_list - list of split hours for prepping.
                    If None, an empty list is used
                    (Default: None)

                ex_props - additional properties for describing this consumable. Some used in dialogues in generic labels.
                    If None, an empty dict is used, and fallback text will be shown
                    (Default: None)

                should_restock_warn - should Monika warn the player that this needs to be restocked?
                    (Default: True)

                late_entry_list - list of times storing when we should load in with a consumable already out
                    If None, the start times from the start_end_tuple_list are assumed
                    NOTE: must be the same length as start_end_tuple_list
                    (Default: None)

                max_re_serve - amount of times Monika can get a refill of this consumable
                    (Default: None)

                max_stock_amount - maximum amount of this consumable we can stock
                    (Default: 150)

                cons_chance - chance for Monika to continue having this consumable
                    (Default: 80/100)

                cons_low - low bracket for Monika to have this consumable
                    (NOTE: Should be passed in as seconds)
                    (Default: 10 minutes)

                cons_high - high bracket for Monika to have this consumable
                    (NOTE: Should be passed in as seconds)
                    (Default: 2 hours)

                prep_low - low bracket for prep time
                    (NOTE: Should be passed in as seconds)
                    (Default: 2 minutes)
                    NOTE: If set to None, this will not be considered preppable

                prep_high - high bracket for prep time
                    (NOTE: Should be passed in as seconds)
                    (Default: 4 minutes)
                    NOTE: If set to None, this will not be considered preppable

                get_cons_evl - evl to use for getting the consumable. If None, a generic is assumed
                    (Default: None)
                    NOTE: Should have an Event object associated with the label

                finish_prep_evl - evl to use when finished prepping. If None, a generic is assumed
                    (Default: None)
                    NOTE: Should have an Event object associated with the label

                finish_cons_evl - evl to use when finished consuming. If None, a generic is assumed
                    (Default: None)
                    NOTE: Should have an Event object associated with the label
            """
            if (
                consumable_type in store.mas_consumables.consumable_map
                and consumable_id in store.mas_consumables.consumable_map[consumable_type]
            ):
                raise Exception("Consumable {0} already exists.".format(consumable_id))

            self.consumable_id = consumable_id
            self.consumable_type = consumable_type
            self.disp_name = disp_name
            self.start_end_tuple_list = start_end_tuple_list

            if mas_consumables.CONS_FULL not in acs_map:
                raise Exception("Consumable {0} is missing the required 'full' key in its acs map.".format(consumable_id))
            if mas_consumables.CONS_HALFDONE not in acs_map:
                acs_map[mas_consumables.CONS_HALFDONE] = acs_map[mas_consumables.CONS_FULL]
            if mas_consumables.CONS_DONE not in acs_map:
                acs_map[mas_consumables.CONS_DONE] = acs_map[mas_consumables.CONS_HALFDONE]

            self.acs_map = acs_map
            self.acs = acs_map[mas_consumables.CONS_FULL]

            self.cons_chance = cons_chance
            self.cons_low = cons_low
            self.cons_high = cons_high

            if late_entry_list is None:
                self.late_entry_list = list()

                for start, end in start_end_tuple_list:
                    self.late_entry_list.append(start)
            else:
                self.late_entry_list = late_entry_list

            self.max_re_serve = max_re_serve
            self.max_stock_amount = max_stock_amount
            self.re_serves_had = 0

            self.ex_props = ex_props if ex_props else dict()
            self.split_list = split_list
            self.should_restock_warn = should_restock_warn
            self.prep_low = prep_low
            self.prep_high = prep_high

            #EVLs:
            if consumable_type == 0:
                self.get_cons_evl = get_cons_evl if get_cons_evl is not None else MASConsumable.DRINK_GET_EVL
                self.finish_prep_evl = finish_prep_evl if finish_prep_evl is not None else MASConsumable.BREW_FINISH_EVL
                self.finish_cons_evl = finish_cons_evl if finish_cons_evl is not None else MASConsumable.DRINK_FINISH_EVL
            else:
                self.get_cons_evl = get_cons_evl if get_cons_evl is not None else MASConsumable.FOOD_GET_EVL
                self.finish_prep_evl = finish_prep_evl if finish_prep_evl is not None else MASConsumable.PREP_FINISH_EVL
                self.finish_cons_evl = finish_cons_evl if finish_cons_evl is not None else MASConsumable.FOOD_FINISH_EVL

            #Timeout prop
            self.done_cons_until = None

            #Add this to the map
            if consumable_type not in store.mas_consumables.consumable_map:
                store.mas_consumables.consumable_map[consumable_type] = dict()

            store.mas_consumables.consumable_map[consumable_type][consumable_id] = self

            #Now we need to set up data if not already set
            if consumable_id not in persistent._mas_consumable_map:
                persistent._mas_consumable_map[consumable_id] = {
                    "enabled": False,
                    "times_had": 0,
                    "servings_left": 0,
                    "has_restock_warned": False,
                    "last_had": None
                }

        def __repr__(self):
            """
            Representation of this obj
            """
            return "<MASConsumable: (id: '{0}', {1}, stock: {2}/{3})>".format(
                self.consumable_id,
                "is enabled" if self.enabled() else "is disabled",
                self.getStock(),
                self.max_stock_amount
            )

        def enabled(self):
            """
            Checks if this consumable is enabled

            OUT:
                boolean:
                    - True if this consumable is enabled
                    - False otherwise
            """
            return persistent._mas_consumable_map[self.consumable_id]["enabled"]

        def enable(self):
            """
            Enables the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["enabled"] = True

        def disable(self):
            """
            Disables the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["enabled"] = False

        def increment(self):
            """
            Increments the amount of times Monika has had the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["times_had"] += 1

        @property
        def last_had(self):
            """
            Getter for last_had
            """
            return persistent._mas_consumable_map[self.consumable_id]["last_had"]

        @last_had.setter
        def last_had(self, value):
            """
            Setter for last_had

            IN:
                value - value for this prop (assuming datetime.datetime)
            """
            persistent._mas_consumable_map[self.consumable_id]["last_had"] = value

        def shouldHave(self, _now=None):
            """
            Checks if we should have this consumable now

            CONDITIONS:
                1. We're within the consumable time range
                2. We pass the chance check to have this consumable
                3. We have not met/exceeded the maximum re-serve amount

            IN:
                _now - datetime.datetime to check if we're within the timerange for this consumable
                If None, now is assumed
                (Default: None)

            OUT:
                boolean:
                    - True if we should have this consumable (passes above conditions)
                    - False otherwise

            NOTE: This does NOT anticipate splits/preparation
            """
            #First, let's check if we've reached the max re-serve point
            if self.max_re_serve is not None and self.re_serves_had == self.max_re_serve:
                return False

            if _now is None:
                _now = datetime.datetime.now()

            _chance = random.randint(1, 100)

            for start_time, end_time in self.start_end_tuple_list:
                if start_time <= _now.hour < end_time and _chance <= self.cons_chance:
                    return True
            return False

        def hasServing(self):
            """
            Checks if we have a serving of this consumable in order to use it

            OUT:
                boolean:
                    - True if we have at least 1 serving left of the consumable
                    - False otherwise
            """
            return persistent._mas_consumable_map[self.consumable_id]["servings_left"] > 0

        def restock(self, servings=100, clear_flag=True):
            """
            Adds more servings of the consumable, protected by max_stock_amount

            IN:
                servings - amount of servings to add
                (Default: 100)
                clear_flag - whether or not we should clear the has_restock_warned flag
                (Default: True)
            """
            max_to_add = self.max_stock_amount - self.getStock()

            #Verify we're not going to go over the max
            servings = max_to_add if servings > max_to_add else servings

            persistent._mas_consumable_map[self.consumable_id]["servings_left"] += servings

            if clear_flag:
                self.resetRestockWarnFlag()

        def getStock(self):
            """
            Gets the amount of servings left of a consumable

            OUT:
                integer:
                    - The amount of servings left for the consumable
            """
            return persistent._mas_consumable_map[self.consumable_id]["servings_left"]

        def isMaxedStock(self):
            """
            Checks if the current stock of the consumable is the max

            OUT:
                boolean:
                    - True if stock is maxed
                    - False otherwise
            """
            return self.getStock() == self.max_stock_amount

        def getAmountHad(self):
            """
            Gets the amount of servings Monika has had of the consumable

            OUT:
                integer:
                    - The amount of times Monika has had the consumable
            """
            return persistent._mas_consumable_map[self.consumable_id]["times_had"]

        def isLow(self):
            """
            Checks if we're running low on a consumable

            OUT:
                boolean:
                    - True if we're less than or equal to the LOW_STOCK_AMT value
                    - False otherwise
            """
            return self.getStock() <= MASConsumable.LOW_STOCK_AMT

        def isCriticalLow(self):
            """
            Checks if we're critically low on a consumable

            OUT:
                boolean:
                    - True if we're less than or equal to the LOW_CRITICAL_STOCK_AMT value
                    - False otherwise
            """
            return self.getStock() <= MASConsumable.LOW_CRITICAL_STOCK_AMT

        def flagRestockWarn(self):
            """
            Flags a consumable as having been restock warned
            """
            persistent._mas_consumable_map[self.consumable_id]["has_restock_warned"] = True

        def resetRestockWarnFlag(self):
            """
            Resets the restock warn flag
            """
            persistent._mas_consumable_map[self.consumable_id]["has_restock_warned"] = False

        def hasRestockWarned(self):
            """
            Return the has restock warned flag
            """
            return persistent._mas_consumable_map[self.consumable_id]["has_restock_warned"]

        def use(self, amount=1, set_last_had=True, set_acs=True):
            """
            Uses a serving of this consumable

            IN:
                amount - amount of servings to use up
                    (Default: 1)
                set_last_had - whether we update the last_had prop or not
                    (Default: True)
                set_acs - whether we update the acs for this cons or not
                    NOTE: you'd probably need to do this manually if you don't call use
                    (Default: True)
            """
            servings_left = persistent._mas_consumable_map[self.consumable_id]["servings_left"]

            if servings_left - amount < 0:
                persistent._mas_consumable_map[self.consumable_id]["servings_left"] = 0
            else:
                persistent._mas_consumable_map[self.consumable_id]["servings_left"] -= amount

            if set_last_had:
                self.last_had = datetime.datetime.now()

            if set_acs:
                self.acs = self.acs_map[mas_consumables.CONS_FULL]

        def re_serve(self):
            """
            Increments the re-serve count
            """
            self.re_serves_had += 1

        def isLateEntry(self, _now=None):
            """
            Checks if we should load with a consumable already out or not

            IN:
                _now - datetime.datetime to check if we're within the time for the consumable
                If None, now is assumed
                (Default: None)

            OUT:
                boolean:
                    - True if we should load in with consumable already out
                    - False otherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            for index in range(len(self.start_end_tuple_list)):
                #Bit of setup
                _start, _end = self.start_end_tuple_list[index]
                late_hour = self.late_entry_list[index]

                if (
                    _start <= _now.hour < _end
                    and _now.hour >= late_hour
                ):
                    return True
            return False

        def prepare(self, _start_time=None):
            """
            Starts preparing the consumable
            (Sets up the finished preparing event)

            IN:
                _start_time - time to start prepping. If none, now is assumed
            """
            if _start_time is None:
                _start_time = datetime.datetime.now()

            #Start prep
            persistent._mas_current_consumable[self.consumable_type]["prep_time"] = _start_time

            #Calculate end prep time
            end_prep = random.randint(self.prep_low, self.prep_high)

            #Setup the event conditional
            mas_setEVLPropValues(
                self.finish_prep_evl,
                conditional=(
                    "persistent._mas_current_consumable[{0}]['prep_time'] is not None "
                    "and (datetime.datetime.now() - "
                    "persistent._mas_current_consumable[{0}]['prep_time']) "
                    "> datetime.timedelta(0, {1})"
                ).format(self.consumable_type, end_prep),
                action=EV_ACT_QUEUE
            )

            #Now we set what we're having
            persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id

        def have(self, _start_time=None, skip_leadin=False):
            """
            Allows Monika to have this consumable
            (Sets up the finished consumable event)

            IN:
                _start_time - time to start prepping. If none, now is assumed
                skip_leadin - whether or not we should push the event where Monika gets something to have
            """
            if _start_time is None:
                _start_time = datetime.datetime.now()

            #Delta for having this cons
            consumable_time = datetime.timedelta(0, random.randint(self.cons_low, self.cons_high))

            #Setup the stop time for the cup
            persistent._mas_current_consumable[self.consumable_type]["consume_time"] = _start_time + consumable_time

            #Setup the event conditional
            mas_setEVLPropValues(
                self.finish_cons_evl,
                conditional=(
                    "persistent._mas_current_consumable[{0}]['consume_time'] is not None "
                    "and datetime.datetime.now() > persistent._mas_current_consumable[{0}]['consume_time']"
                ).format(self.consumable_type),
                action=EV_ACT_QUEUE
            )

            #Skipping leadin? We need to set this to persistent and wear the acs for it
            if skip_leadin:
                persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id
                monika_chr.wear_acs(self.acs)

            #If this isn't a prepable type and we don't have a current consumable of this type, we should push the ev
            elif not self.prepable() and not MASConsumable.__getCurrentConsumable(self.consumable_type):
                persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id
                queueEvent(self.get_cons_evl)

            #Increment cup count
            self.increment()

        def isConsTime(self, _now=None):
            """
            Checks if we're in the time range for this consumable

            IN:
                _now - datetime.datetime to check if we're within the time for
                    If None, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're within the consumable time(s) of this consumable
                    - False otherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            for start_time, end_time in self.start_end_tuple_list:
                if start_time <= _now.hour < end_time:
                    return True
            return False

        def shouldPrep(self, _now=None):
            """
            Checks if we're in the time range for this consumable and we should prepare it

            IN:
                _time - datetime.datetime to check if we're within the time for
                    If none, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're within the preparation time(s) of this consumable (and consumable is preparable)
                    - False otherwise
            """
            if not self.prepable():
                return False

            if _now is None:
                _now = datetime.datetime.now()

            _chance = random.randint(1, 100)

            for split in self.split_list:
                if _now.hour < split and _chance <= self.cons_chance:
                    return True
            return False

        def prepable(self):
            """
            Checks if this consumable is preparable

            OUT:
                boolean:
                    - True if this consumable has:
                        1. prep_high
                        2. prep_low

                    - False otherwise
            """
            return self.prep_low is not None and self.prep_high is not None

        def checkCanHave(self, _now=None):
            """
            Checks if we can have this consumable again

            IN:
                _now - datetime.datetime to check against
                    If None, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we can have this consumable
                    - False otherwise
            """
            #First, if this is None, we return True
            if self.done_cons_until is None:
                return True

            #Otherwise, we need to do a comparison
            elif _now is None:
                _now = datetime.datetime.now()

            if _now >= self.done_cons_until:
                self.done_cons_until = None
                return True
            return False

        @classmethod
        def __getCurrentConsProgress(cls, _type):
            """
            Returns progress for the current consumable of _type
            (0.0 - just started, 1.0 - finished)

            IN:
                _type - the type of consumable to check

            OUT:
                float, the percentage of progress of having the consumable,
                OR None if Monika isn't having anything
            """
            curr_cons = cls.__getCurrentConsumable(_type)
            if not curr_cons:
                return None

            _now = datetime.datetime.now()
            start_time = curr_cons.last_had
            end_time = persistent._mas_current_consumable[_type]["consume_time"]

            if end_time is None or start_time == end_time:
                return 1.0

            progress = round(1.0 - float((end_time - _now).total_seconds()) / (end_time - start_time).total_seconds(), 2)

            return min(max(progress, 0.0), 1.0)

        @classmethod
        def _getCurrentDrinkProgress(cls):
            """
            Returns progress for the current drink

            OUT:
                int, the percentage of progress of having the drink,
                OR None if Monika isn't drinking anything
            """
            return cls.__getCurrentConsProgress(mas_consumables.TYPE_DRINK)

        @classmethod
        def _getCurrentFoodProgress(cls):
            """
           Returns progress for the current food

            OUT:
                int, the percentage of progress of having the food,
                OR None if Monika isn't eating anything
            """
            return cls.__getCurrentConsProgress(mas_consumables.TYPE_FOOD)

        @classmethod
        def validateConsAcs(cls):
            """
            Sets appropriate acs for the current consumables (both types)
            """
            for _type in mas_consumables.consumable_map.iterkeys():
                curr_cons = cls.__getCurrentConsumable(_type)
                if curr_cons is not None:
                    curr_cons_progress = cls.__getCurrentConsProgress(_type)
                    if curr_cons_progress is not None:
                        if 0.65 >= curr_cons_progress:
                            appropriate_acs = curr_cons.acs_map[mas_consumables.CONS_FULL]

                        elif 0.9 >= curr_cons_progress:
                            appropriate_acs = curr_cons.acs_map[mas_consumables.CONS_HALFDONE]

                        else:
                            appropriate_acs = curr_cons.acs_map[mas_consumables.CONS_DONE]

                        if curr_cons.acs is not appropriate_acs:
                            monika_chr.remove_acs(curr_cons.acs)
                            curr_cons.acs = appropriate_acs
                            monika_chr.wear_acs(curr_cons.acs)

        @staticmethod
        def _isStillCons(_type, _now=None):
            """
            Checks if we're still having something

            IN:
                _type - Type of consumable to check for
                    0 - Drink
                    1 - Food

                _now - datetime.datetime object representing current time
                    If none, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're still having something
                    - False otdherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            _time = persistent._mas_current_consumable[_type]["consume_time"]
            return _time is not None and _now < _time

        @staticmethod
        def _getLowCons(critical=False):
            """
            Gets a list of all consumables which Monika is low on, regardless of type (and should warn about)

            IN:
                - critical - Whether this list should only be populated by items Monika is critically low on or not
                    (Default: False)

            OUT:
                list of all consumables Monika is low on (or critical on)
            """
            low_cons = []
            for _type in store.mas_consumables.consumable_map.iterkeys():
                low_cons += MASConsumable._getLowConsType(_type, critical)

            return low_cons

        @staticmethod
        def _getLowConsNotWarned(critical=False):
            """
            Gets a list of all consumables which Monika is low on that she's not restock warned

            IN:
                - critical - Whether this list should only be populated by items Monika is critically low on or not
                    (Default: False)

            OUT:
                list of all consumables Monika
            """
            low_cons = []
            for _type in store.mas_consumables.consumable_map.iterkeys():
                low_cons += MASConsumable._getLowConsType(_type, critical, exclude_restock_warned=True)

            return low_cons

        @staticmethod
        def _getLowConsType(_type, critical=False, exclude_restock_warned=False):
            """
            Gets a list of all consumables (of the provided type) which Monika is low on (and should warn about)

            IN:
                _type - Type of consumables to get a low list for
                critical - Whether the list should be only those Monika is critically low on
                    (Default: False)
                exclude_restock_warned - Whether or not we want to exclude consumables we've restock warned already
                    (Default: False)

            OUT:
                list of all consumables of the provided type Monika is low on (or critical on), matching the entered criteria
            """
            if _type not in store.mas_consumables.consumable_map:
                return []

            if critical:
                if exclude_restock_warned:
                    return [
                        cons
                        for cons in store.mas_consumables.consumable_map[_type].itervalues()
                        if cons.enabled() and cons.should_restock_warn and cons.isCriticalLow() and not cons.hasRestockWarned()
                    ]

                else:
                    return [
                        cons
                        for cons in store.mas_consumables.consumable_map[_type].itervalues()
                        if cons.enabled() and cons.should_restock_warn and cons.isCriticalLow()
                    ]

            else:
                if exclude_restock_warned:
                    return [
                        cons
                        for cons in store.mas_consumables.consumable_map[_type].itervalues()
                        if cons.enabled() and cons.should_restock_warn and cons.isLow() and not cons.hasRestockWarned()
                    ]

                else:
                    return [
                        cons
                        for cons in store.mas_consumables.consumable_map[_type].itervalues()
                        if cons.enabled() and cons.should_restock_warn and cons.isLow()
                    ]

        @staticmethod
        def _reset(_type=None):
            """
            Resets the events for the consumable and resets the current consumable(s)

            IN:
                _type - Type of consumable to reset events for
                    (If None, all types are reset. Default: None)
            """
            def cons_reset(consumable):
                """
                Resets the labels for the current consumables

                IN:
                    consumable - consumable object to reset
                """
                if consumable is None:
                    return

                monika_chr.remove_acs(consumable.acs)
                consumable.re_serves_had = 0

                #Strip EVs
                mas_stripEVL(consumable.get_cons_evl, list_pop=True)
                mas_stripEVL(consumable.finish_prep_evl, list_pop=True)
                mas_stripEVL(consumable.finish_cons_evl, list_pop=True)

                #Now reset the persist var for this type
                persistent._mas_current_consumable[consumable.consumable_type] = {
                    "prep_time": None,
                    "consume_time": None,
                    "id": None
                }

            #Get current consumables and reset
            if _type == 0 or _type is None:
                cons_reset(MASConsumable._getCurrentDrink())

            if _type ==1 or _type is None:
                cons_reset(MASConsumable._getCurrentFood())

        @staticmethod
        def __shouldReset(_type, curr_cons, available_cons):
            """
            Checks if we should reset the current consumable type

            CONDITIONS:
                1. We're having a consumable we shouldn't be having now and we opened the game after its consume time or
                2. We're still prepping something but
                    - The consumable's finish prepping event doesn't have conditionals or
                    - It's no longer time for this consumable

            IN:
                _type - type of consumable to reset
                curr_cons - current_consumable (of _type)
                available_cons - available consumables for the current time

            OUT:
                boolean:
                    - True if we should reset the current consumable type
                    - False otherwise
            """
            #If we have no consumable, then there's no point in doing anything
            if not curr_cons:
                return False

            return (
                (
                    MASConsumable._isHaving(_type)
                    and (
                        not MASConsumable._isStillCons(_type)
                        and mas_getCurrSeshStart() > persistent._mas_current_consumable[_type]["consume_time"]
                    )
                )
                or (
                    persistent._mas_current_consumable[_type]["prep_time"] is not None
                    and (
                        mas_checkEVL(curr_cons.finish_prep_evl, lambda x: x.conditional is None)
                        or curr_cons not in available_cons
                    )
                )
            )

        @staticmethod
        def _getCurrentDrink():
            """
            Gets the MASConsumable object for the current drink or None if we're not drinking

            OUT:
                - Current MASConsumable if drinking
                - None if not drinking
            """
            return MASConsumable.__getCurrentConsumable(store.mas_consumables.TYPE_DRINK)

        @staticmethod
        def _getCurrentFood():
            """
            Gets the MASConsumable object for the current food or None if we're not eating

            OUT:
                - Current MASConsumable if eating
                - None if not eating
            """
            return MASConsumable.__getCurrentConsumable(store.mas_consumables.TYPE_FOOD)

        @staticmethod
        def _isHaving(_type):
            """
            Checks if we're currently drinking something right now

            IN:
                _type - integer representing the consumable type

            OUT:
                boolean:
                    - True if we have a current consumable of _type and consume time
                    - False otherwise
            """
            return (
                bool(
                    persistent._mas_current_consumable[_type]["id"]
                    and persistent._mas_current_consumable[_type]["consume_time"]
                )
            )

        @staticmethod
        def _getConsumablesForTime(_type):
            """
            Gets a list of all consumable drinks active at this time

            IN:
                _type - type of consumables to get

            OUT:
                list of consumable objects of _type enabled and within time range
            """
            if _type not in store.mas_consumables.consumable_map:
                return []

            return [
                cons
                for cons in mas_consumables.consumable_map[_type].itervalues()
                if cons.enabled() and cons.hasServing() and cons.checkCanHave() and cons.isConsTime()
            ]

        @staticmethod
        def _validatePersistentData(_type):
            """
            Verifies that the data stored in persistent._mas_current_consumable is valid to the consumables currently set up

            IN:
                _type - type of consumable to validate persistent data for

            NOTE: If the persistent data stored isn't valid, it is reset.
            """
            if MASConsumable._isHaving(_type) and not MASConsumable.__getCurrentConsumable(_type):
                persistent._mas_current_consumable[_type] = {
                    "prep_time": None,
                    "consume_time": None,
                    "id": None
                }

        @staticmethod
        def _checkConsumables(startup=False):
            """
            Logic to handle Monika having a consumable both on startup and during runtime

            IN:
                startup - Whether or not we should check for a late entry
                (Default: False)
            """
            MASConsumable.__checkingLogic(
                _type=store.mas_consumables.TYPE_DRINK,
                curr_cons=MASConsumable._getCurrentDrink(),
                startup=startup
            )

            MASConsumable.__checkingLogic(
                _type=store.mas_consumables.TYPE_FOOD,
                curr_cons=MASConsumable._getCurrentFood(),
                startup=startup
            )

            if startup and not store.mas_globals.returned_home_this_sesh:
                MASConsumable._absentUse()

                #Now we'll check if we've got sprites out in case we've crashed
                drink_acs = store.monika_chr.get_acs_of_exprop(store.mas_sprites.EXP_A_DRINK)
                food_acs = store.monika_chr.get_acs_of_exprop(store.mas_sprites.EXP_A_FOOD)

                #Remove if we need to
                if not MASConsumable._isHaving(store.mas_consumables.TYPE_DRINK) and drink_acs:
                    store.monika_chr.remove_acs(drink_acs)

                if not MASConsumable._isHaving(store.mas_consumables.TYPE_FOOD) and food_acs:
                    store.monika_chr.remove_acs(food_acs)

                #We should warn if there's something to warn about
                if MASConsumable._getLowConsNotWarned():
                    store.queueEvent("mas_consumables_generic_running_out_absentuse")

        @staticmethod
        def _absentUse():
            """
            Runs a check on all consumables and subtracts the amount used in the player's absence
            """
            def calculate_and_use(consumable, servings, days_absent, now):
                """
                Checks how many servings of the consumable Monika will have used in the player's absence

                IN:
                    consumable - consumable to use
                    servings - amount of servings per having of the consumable
                    days_absent - amount of days the player was absent
                    now - current datetime
                """
                for day in range(days_absent):
                    if random.randint(1, 100) <= consumable.cons_chance:
                        consumable.use(servings, set_last_had=False, set_acs=False)
                        cons.last_had = now - datetime.timedelta(days=days_absent-day)

            consumables = MASConsumable._getEnabledConsumables()
            _days = mas_getAbsenceLength().days
            _now = datetime.datetime.now()

            for cons in consumables:
                if cons.prepable():
                    calculate_and_use(consumable=cons, servings=random.randint(3,5), days_absent=_days, now=_now)
                else:
                    calculate_and_use(consumable=cons, servings=4, days_absent=_days, now=_now)

        @staticmethod
        def _getEnabledConsumables():
            """
            Gets all enabled consumables

            OUT:
                List of MASConsumable objects which are enabled

            NOTE: enabled is regardless of stock amount
            """
            consumables = []

            if store.mas_consumables.TYPE_DRINK in store.mas_consumables.consumable_map:
                consumables.extend([
                    drink
                    for drink in store.mas_consumables.consumable_map[mas_consumables.TYPE_DRINK].values()
                    if drink.enabled()
                ])

            if store.mas_consumables.TYPE_FOOD in store.mas_consumables.consumable_map:
                consumables.extend([
                    food
                    for food in store.mas_consumables.consumable_map[mas_consumables.TYPE_FOOD].values()
                    if food.enabled()
                ])

            return consumables

        @staticmethod
        def __getCurrentConsumable(_type):
            """
            Gets the current consumable, provided by type

            IN:
                _type - consumable type to get the current consumable for

            OUT:
                MASConsumable object representing the current consumable object for the type
                If there's no consumable out by _type, None is returned
            """
            return mas_getConsumable(
                persistent._mas_current_consumable[_type]["id"]
            )

        @staticmethod
        def __checkingLogic(_type, curr_cons, startup):
            """
            Generalized logic to check if we should have a consumable

            IN:
                _type - consumable type
                curr_cons - current_consumable (of _type)
                startup - whether or not to perform a startup check
            """
            available_cons = MASConsumable._getConsumablesForTime(_type)

            #Verify persist data
            MASConsumable._validatePersistentData(_type)

            #Check if we should reset the current consumable type
            if MASConsumable.__shouldReset(_type, curr_cons, available_cons):
                MASConsumable._reset(_type)

            #If we're currently prepping/having anything, we don't need to do anything else
            if persistent._mas_current_consumable[_type]["id"] is not None:
                #Wear the acs if we don't have it out for some reason
                if MASConsumable._isHaving(_type) and not monika_chr.is_wearing_acs(curr_cons.acs):
                    monika_chr.wear_acs(curr_cons.acs)
                return

            #If we have no consumables, then there's no point in doing anything
            if not available_cons:
                return

            #Otherwise, step two: what are we having?
            cons = random.choice(available_cons)

            #Setup some vars
            _now = datetime.datetime.now()

            #Time to C O N S U M E
            #First, clear vars so we start fresh
            MASConsumable._reset(_type)

            #First, should we even have this?
            if cons.shouldHave():
                #If we prepare, we prep using 3-5 chages worth (to acct for multiple servings)
                if cons.prepable():
                    cons.use(amount=random.randint(3,5))

                #Otherwise, if it's a non-prepable, just one
                else:
                    cons.use()

                #Are we loading in after the time? If so, we should already have the cons out. No prep, just have
                #Though we'll not guarantee this to add a degree of realism/variance (80% chance she'll start with it out)
                if startup and cons.isLateEntry() and random.randint(1, 100) <= 80:
                    cons.have(skip_leadin=True)

                else:
                    #If this is a prepable, we should prep it
                    if cons.prepable() and cons.shouldPrep(_now):
                        cons.prepare()

                    #Otherwise, we'll just set up having it
                    elif not cons.prepable():
                        cons.have()

#END: MASConsumable class

    #START: Global functions
    def mas_generateShoppingList(low_cons_list=None):
        """
        Generates a list of consumables we're low on in the form of a 'shopping list'
        and exports it to the characters folder

        IN:
            low_cons_list - List of MASConsumable objects that we're low on
            If None, we get it here
            (Default: None)
        """
        #First, get all the consumables we're low on if not provided
        if low_cons_list is None:
            low_cons_list = MASConsumable._getLowCons()

        START_TEXT = (
            "Hi, [player],\n"
            "Just letting you know I'm running low on a couple of things.\n"
            "You wouldn't mind getting some more for me, would you?\n\n"
            "Here's a list of what I'm running out of:\n"
        )

        MID_TEXT = ""

        END_TEXT = (
            "Thanks, [player]~"
        )

        for cons in low_cons_list:
            MID_TEXT += "- {0}\n".format(cons.disp_name.capitalize())

        MID_TEXT += "\n"

        with open(renpy.config.basedir + "/characters/shopping_list.txt", "w") as shopping_list:
            shopping_list.write(
                renpy.substitute(START_TEXT + MID_TEXT + END_TEXT)
            )

    def mas_getConsumable(consumable_id):
        """
        Gets a consumable object by type and id

        IN:
            consumable_id - id of the consumable

        OUT:
            Consumable object:
                If found, MASConsumable
                If not found, None
        """
        for consumable_type in store.mas_consumables.consumable_map.keys():
            if consumable_id in store.mas_consumables.consumable_map[consumable_type]:
                return store.mas_consumables.consumable_map[consumable_type][consumable_id]
        return None

    def mas_useThermos():
        """
        Gets Monika to put her drink into a thermos when taking her somewhere if it is eligible
        """
        #Firstly, if we're already wearing a thermos, we should do nothing
        if monika_chr.is_wearing_acs_type("thermos-mug"):
            return

        #Otherwise, if we have a drink out that's portable, let's put it in a thermos so we can take it when we leave
        current_drink = MASConsumable._getCurrentDrink()
        if current_drink and current_drink.ex_props.get(mas_consumables.PROP_PORTABLE, False):
            #We have a current drink. Let's get all accessories of this type so we can essentially spritepack them
            thermoses = [thermos.get_sprobj() for thermos in mas_selspr.filter_acs(True, "thermos-mug")]

            #If we have an unlocked thermos, we'll use it here
            if thermoses:
                thermos = renpy.random.choice(thermoses)
                monika_chr.wear_acs(thermos)

#START: Consumable drink defs
init 6 python:
    MASConsumable(
        consumable_id="coffee",
        consumable_type=store.mas_consumables.TYPE_DRINK,
        disp_name="coffee",
        ex_props=mas_consumables.PREP_HOT_DRINK,
        start_end_tuple_list=[(5, 12)],
        acs_map={mas_consumables.CONS_FULL: mas_acs_mug},
        split_list=[11],
        late_entry_list=[10],
        max_re_serve=3
    )

    MASConsumable(
        consumable_id="hotchoc",
        consumable_type=store.mas_consumables.TYPE_DRINK,
        disp_name="hot chocolate",
        ex_props=mas_consumables.PREP_HOT_DRINK,
        start_end_tuple_list=[(16, 23)],
        acs_map={mas_consumables.CONS_FULL: mas_acs_hotchoc_mug},
        split_list=[22],
        late_entry_list=[19],
        max_re_serve=3
    )
#END: Consumable drink defs

#START: Consumable food defs
    MASConsumable(
        consumable_id="candycane",
        consumable_type=store.mas_consumables.TYPE_FOOD,
        disp_name="candycane",
        ex_props={
            mas_consumables.PROP_PLUR: True,
            mas_consumables.PROP_AMOUNT_REF: mas_consumables.AMOUNT_SOME
        },
        start_end_tuple_list=[(11, 13), (16, 20)],
        acs_map={mas_consumables.CONS_FULL: mas_acs_candycane},
        late_entry_list=[12, 19],
        max_re_serve=1,
        should_restock_warn=False,
        max_stock_amount=18,
        prep_low=None,
        cons_high=15*60, #15 minute max
        # TODO: this is temp, we need to generalize cons w/o finishig dlg
        finish_cons_evl="mas_consumables_candycane_finish_having"
    )

    MASConsumable(
        consumable_id="christmascookies",
        consumable_type=store.mas_consumables.TYPE_FOOD,
        disp_name="Christmas cookie",
        ex_props={
            mas_consumables.PROP_OBJ_REF: mas_consumables.CONTAINER_PLATE,
            mas_consumables.PROP_AMOUNT_REF: mas_consumables.AMOUNT_SOME,
            mas_consumables.PROP_PLUR: True,
            mas_consumables.PROP_COMPATIBLE: True
        },
        start_end_tuple_list=[(5, 12), (16, 23)],
        acs_map={mas_consumables.CONS_FULL: mas_acs_christmascookies},
        late_entry_list=[11, 19],
        max_re_serve=2,
        should_restock_warn=False,
        max_stock_amount=20,
        prep_low=None,
        cons_high=30*60 #30 minute max
    )

    MASConsumable(
        consumable_id="cupcake",
        consumable_type=store.mas_consumables.TYPE_FOOD,
        disp_name="cupcake",
        ex_props=mas_consumables.NON_PREP_PASTRY,
        start_end_tuple_list=[(5, 12), (16, 23)],
        # Choose one at random on startup
        acs_map={mas_consumables.CONS_FULL: random.choice((mas_acs_cupcake_smug, mas_acs_cupcake_owo, mas_acs_cupcake_uwu))},
        late_entry_list=[11, 19],
        max_re_serve=1,
        should_restock_warn=False,
        max_stock_amount=6,
        prep_low=None,
        cons_high=30*60
    )

    MASConsumable(
        consumable_id="cinnamon_bun",
        consumable_type=store.mas_consumables.TYPE_FOOD,
        disp_name="cinnamon bun",
        ex_props=mas_consumables.NON_PREP_PASTRY,
        start_end_tuple_list=[(5, 12), (16, 23)],
        acs_map={
            mas_consumables.CONS_FULL: mas_acs_cinnamon_bun,
            mas_consumables.CONS_DONE: mas_acs_empty_plate
        },
        should_restock_warn=False,
        late_entry_list=[11, 19],
        max_re_serve=0,
        max_stock_amount=6,
        prep_low=None,
        prep_high=None,
        cons_high=30*60
    )

    MASConsumable(
        consumable_id="cherry_cheesecake",
        consumable_type=store.mas_consumables.TYPE_FOOD,
        disp_name="cherry cheesecake",
        ex_props=mas_consumables.NON_PREP_CAKE,
        start_end_tuple_list=[(5, 12), (16, 23)],
        acs_map={
            mas_consumables.CONS_FULL: mas_acs_cherry_cheesecake,
            mas_consumables.CONS_DONE: mas_acs_empty_plate
        },
        should_restock_warn=False,
        late_entry_list=[11, 19],
        max_re_serve=1,
        max_stock_amount=8,
        prep_low=None,
        prep_high=None,
        cons_high=30*60
    )
#END: Consumable food defs

#START: Finished brewing/drinking evs
##Finished brewing
init 5 python:
    #This event gets its params via _checkConsumables()
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_brewing",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_finished_brewing:
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finished_prepping(consumable=current_drink)
    return

###Drinking done
init 5 python:
    #Like finshed_brewing, this event gets its params from consumable logic
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_drinking",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_finished_drinking:
    #Get the current drink and see how we should act here
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finish_having(consumable=current_drink)
    return

##Get drink
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_get_drink",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_get_drink:
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_get(consumable=current_drink)
    return
#END: Generic drink evs

#START: Generic food evs
init 5 python:
    #This event gets its params via consumable logic
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_prepping",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_finished_prepping:
    $ current_food = MASConsumable._getCurrentFood()
    call mas_consumables_generic_finished_prepping(consumable=current_food)
    return

###Eating done
init 5 python:
    #Like finshed_brewing, this event gets its params from
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_eating",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_finished_eating:
    #Get the current drink and see how we should act here
    $ current_food = MASConsumable._getCurrentFood()
    call mas_consumables_generic_finish_having(consumable=current_food)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_get_food",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_get_food:
    $ current_food = MASConsumable._getCurrentFood()
    call mas_consumables_generic_get(consumable=current_food)
    return
#END: Generic food evs

# TODO: actually, this label could get a second arg that would tell us what we need to do (get/put away, etc)
label mas_consumables_handling(consumable):
    # We got a consumable to handle
    # First, decide WHAT we need to do with it: finish prep, get, put away
    # TODO: start prep event
    python:
        now = datetime.datetime.now()
        has_plushie_out = monika_chr.is_wearing_acs(mas_acs_quetzalplushie)

        consumable_container_ref = consumable.ex_props.get(mas_consumables.PROP_CONTAINER_REF)
        consumable_obj_ref = consumable.ex_props.get(mas_consumables.PROP_OBJ_REF)
        consumable_amount_ref = consumable.ex_props.get(mas_consumables.PROP_AMOUNT_REF)
        consumable_plur = "s" if consumable.ex_props.get(mas_consumables.PROP_PLUR, False) else ""
        # TODO: add methods for this
        consume_time = persistent._mas_current_consumable[consumable.consumable_type]["consume_time"]
        prep_time = persistent._mas_current_consumable[consumable.consumable_type]["prep_time"]

        paired_consumable = MASConsumable.__getCurrentConsumable(not consumable.consumable_type)
        if paired_consumable is not None:
            paired_consumable_container_ref = paired_consumable.ex_props.get(mas_consumables.PROP_CONTAINER_REF)
            paired_consumable_obj_ref = paired_consumable.ex_props.get(mas_consumables.PROP_OBJ_REF)
            paired_consumable_amount_ref = paired_consumable.ex_props.get(mas_consumables.PROP_AMOUNT_REF)
            paired_consumable_plur = "s" if paired_consumable.ex_props.get(mas_consumables.PROP_PLUR, False) else ""
            pc_consume_time = persistent._mas_current_consumable[paired_consumable.consumable_type]["consume_time"]
            pc_prep_time = persistent._mas_current_consumable[paired_consumable.consumable_type]["prep_time"]

        else:
            paired_consumable_container_ref = None
            paired_consumable_obj_ref = None
            paired_consumable_amount_ref = None
            paired_consumable_plur = None
            pc_consume_time = None
            pc_prep_time = None

        intro = None
        line_start = None
        line_mid = None
        line_end = None

        # Now branch

        # Deal with this consumable
        main_action = None
        # Prepping
        if prep_time is not None:
            # Starting
            if now < prep_time:
                main_action = "starting_prep"

            # Finishing
            else:
                main_action = "finished_prep"

        # Starting/finishing consuming
        elif consume_time is not None:
            # Starting
            if now < consume_time:
                main_action = "getting_cons"

            # Finishing
            else:
                main_action = "finished_cons"

        # Deal with the second consumable
        second_action = None
        # Prepping
        if pc_prep_time is not None:
            # Starting
            if (
                now < pc_prep_time
                and (
                    mas_inEVL(paired_consumable.start_prep_evl)# It's either already queued
                    or mas_getEVLPropValue(paired_consumable.start_prep_evl, "action", None) is not None# Or has an action and will be queued soon
                )
            ):
                second_action = "starting_prep"

            # Finishing
            elif (
                now > pc_prep_time
                and (
                    mas_inEVL(paired_consumable.finish_prep_evl)
                    or mas_getEVLPropValue(paired_consumable.finish_prep_evl, "action", None) is not None
                )
            ):
                second_action = "finished_prep"

        # Starting/finishing consuming
        elif pc_consume_time is not None:
            # Starting
            if (
                now < pc_consume_time
                and (
                    mas_inEVL(paired_consumable.get_cons_evl)
                    or mas_getEVLPropValue(paired_consumable.get_cons_evl, "action", None) is not None
                )
            ):
                second_action = "getting_cons"

            # Finishing
            elif (
                now > pc_consume_time
                and (
                    mas_inEVL(paired_consumable.finish_cons_evl)
                    or mas_getEVLPropValue(paired_consumable.finish_cons_evl, "action", None) is not None
                )
            ):
                second_action = "finished_cons"

    # This should never happen
    if main_action is None:
        return

    elif main_action == "starting_prep":
        if second_action == "starting_prep":
            pass

        elif second_action == "finished_prep":
            pass

        elif second_action == "getting_cons":
            pass

        elif second_action == "finished_cons":
            pass

        # We don't have/need to do anything with the second cons
        else:
            pass

    elif main_action == "finished_prep":
        pass

    elif main_action == "getting_cons":
        python:
            intro = None
            line_start = "I'm going to "

            if second_action == "starting_prep":
                pass

            elif second_action == "finished_prep":
                pass

            elif second_action == "getting_cons":
                pass

            elif second_action == "finished_cons":
                pass

            else:
                pass

    elif main_action == "finished_cons":
        python:
            # In case the acs wasn't updated, we do it here
            cons_done_acs = consumable.acs_map[mas_consumables.CONS_DONE]
            if consumable.acs is not cons_done_acs:
                monika_chr.remove_acs(consumable.acs)
                curr_cons.acs = cons_done_acs
                monika_chr.wear_acs(consumable.acs)

            get_more_consumable = (
                consumable.shouldHave()
                and (consumable.prepable() or (not consumable.prepable() and consumable.hasServing()))
            )

            intro = "I finished my [consumable.disp_name][consumable_plur]."
            line_start = "I'm going to "

            if second_action == "starting_prep":
                pass

            elif second_action == "finished_prep":
                pass

            elif second_action == "getting_cons":
                pass

            elif second_action == "finished_cons":
                pass

            else:
                pass

    return

label mas_consumables_generic_startprep(first_cons, second_cons):
    return

label mas_consumables_generic_finishprep(first_cons, second_cons):
    return

label mas_consumables_generic_get(first_cons, second_cons):
    python:
        intro = None
        line_start = "I'm going to "

        if consumable_container_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(consumable_container_ref)] of [consumable.disp_name][consumable_plur].")

        elif consumable_obj_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(consumable_obj_ref)] of [consumable.disp_name][consumable_plur].")

        else:
            a_an = (consumable_amount_ref or "some") if consumable_plur else mas_a_an(consumable.disp_name, ignore_case=True)
            line_mid = renpy.substitute("get [a_an] [consumable.disp_name][plur].")

        line_end = ""
    return

label mas_consumables_generic_finish(first_cons, second_cons):
    return

label mas_consumables_generic_startprep_and_startprep(first_cons, second_cons):
    return

label mas_consumables_generic_startprep_and_finishprep(first_cons, second_cons):
    return

label mas_consumables_generic_finishprep_and_finishprep(first_cons, second_cons):
    return

label mas_consumables_generic_get_and_get(first_cons, second_cons):
    python:
        intro = None
        line_start = "I'm going to "

        if paired_consumable_container_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(paired_consumable_container_ref)] of [paired_consumable.disp_name][paired_consumable_plur] ")

        elif paired_consumable_obj_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(paired_consumable_obj_ref)] of [paired_consumable.disp_name][paired_consumable_plur] ")

        else:
            a_an = (paired_consumable_amount_ref or "some") if paired_consumable_plur else mas_a_an(paired_consumable.disp_name, ignore_case=True)
            line_mid = renpy.substitute("get [a_an] [paired_consumable.disp_name][paired_consumable_plur] ")

        if consumable_container_ref:
            line_end = renpy.substitute("and [mas_a_an_str(consumable_container_ref)] of [consumable.disp_name][consumable_plur].")

        elif consumable_obj_ref:
            line_end = renpy.substitute("and [mas_a_an_str(consumable_obj_ref)] of [consumable.disp_name][consumable_plur].")

        else:
            a_an = (consumable_amount_ref or "some") if consumable_plur else mas_a_an(consumable.disp_name, ignore_case=True)
            line_end = renpy.substitute("and [a_an] [consumable.disp_name][consumable_plur].")
    return

label mas_consumables_generic_get_and_finish(first_cons, second_cons):
    python:
        # In case the acs wasn't updated, we do it here
        cons_done_acs = paired_consumable.acs_map[mas_consumables.CONS_DONE]
        if paired_consumable.acs is not cons_done_acs:
            monika_chr.remove_acs(paired_consumable.acs)
            curr_cons.acs = cons_done_acs
            monika_chr.wear_acs(paired_consumable.acs)

        get_more_paired_consumable = (
            paired_consumable.shouldHave()
            and (paired_consumable.prepable() or (not paired_consumable.prepable() and paired_consumable.hasServing()))
        )

        intro = renpy.substitute("I finished my [paired_consumable.disp_name][paired_consumable_plur].")
        line_start = "I'm going to "

        if get_more_paired_consumable:
            if paired_consumable_container_ref:
                line_mid = renpy.substitute("get another [paired_consumable_container_ref] ")

            elif paired_consumable_obj_ref:
                line_mid = renpy.substitute("get another [paired_consumable_obj_ref] ")

            else:
                more = "more" if paired_consumable_plur else "another one"
                line_mid = renpy.substitute("get [more] ")

        else:
            if paired_consumable_container_ref:
                line_mid = renpy.substitute("put this [paired_consumable_container_ref] away ")

            # This case is for both paired_consumable_obj_ref and generic else path
            else:
                line_mid = renpy.substitute("put this away ")

        # This works for both paths above
        if consumable_container_ref:
            line_end = renpy.substitute("and grab [mas_a_an_str(consumable_container_ref)] of [consumable.disp_name][consumable_plur].")

        elif consumable_obj_ref:
            line_end = renpy.substitute("and grab [mas_a_an_str(consumable_obj_ref)] of [consumable.disp_name][consumable_plur].")

        else:
            a_an = (consumable_amount_ref or "some") if consumable_plur else mas_a_an(consumable.disp_name, ignore_case=True)
            line_end = renpy.substitute("and grab [a_an] [consumable.disp_name][consumable_plur].")
    return

label mas_consumables_generic_get_and_startprep(first_cons, second_cons):
    python:
        intro = None
        line_start = "I'm going to "

        if second_action == "starting_prep":
            if paired_consumable_amount_ref is not None:
                some = paired_consumable_amount_ref + paired_consumable.disp_name + paired_consumable_plur
            else:
                some = mas_a_an_str(paired_consumable.disp_name) + paired_consumable_plur
            line_mid = renpy.substitute("make [some] ")

            if consumable_container_ref:
                line_end = renpy.substitute("and get [mas_a_an_str(consumable_container_ref)] of [consumable.disp_name][consumable_plur].")

            elif consumable_obj_ref:
                line_end = renpy.substitute("and get [mas_a_an_str(consumable_obj_ref)] of [consumable.disp_name][consumable_plur].")

            else:
                a_an = (consumable_amount_ref or "some") if consumable_plur else mas_a_an(consumable.disp_name, ignore_case=True)
                line_end = renpy.substitute("and get [a_an] [consumable.disp_name][consumable_plur].")
    return

label mas_consumables_generic_get_and_finishprep(first_cons, second_cons):
    python:
        is_are = "are" if plur else "is"
        intro = renpy.substitute("Oh, my [paired_consumable.disp_name][paired_consumable_plur] [is_are] ready.")
        line_start = "I'm going to "

        if paired_consumable_container_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(paired_consumable_container_ref)] ")

        elif paired_consumable_obj_ref:
            line_mid = renpy.substitute("get [mas_a_an_str(paired_consumable_obj_ref)] ")

        else:
            some = (paired_consumable_amount_ref or "some") if paired_consumable_plur else "one"
            line_mid = renpy.substitute("get [some] ")

        if consumable_container_ref:
            line_end = renpy.substitute("along with [mas_a_an_str(consumable_container_ref)] of [consumable.disp_name][consumable_plur].")

        elif consumable_obj_ref:
            line_end = renpy.substitute("along with [mas_a_an_str(consumable_obj_ref)] of [consumable.disp_name][consumable_plur].")

        else:
            a_an = (consumable_amount_ref or "some") if consumable_plur else mas_a_an(consumable.disp_name, ignore_case=True)
            line_end = renpy.substitute("along with [a_an] [consumable.disp_name][consumable_plur].")
    return

label mas_consumables_generic_finish_and_finish(first_cons, second_cons):
    return

label mas_consumables_generic_finish_and_startprep(first_cons, second_cons):
    python:
        # In case the acs wasn't updated, we do it here
        cons_done_acs = first_cons.acs_map[mas_consumables.CONS_DONE]
        if first_cons.acs is not cons_done_acs:
            monika_chr.remove_acs(first_cons.acs)
            first_cons.acs = cons_done_acs
            monika_chr.wear_acs(first_cons.acs)

        get_more_first_cons = (
            first_cons.shouldHave()
            and (first_cons.prepable() or (not first_cons.prepable() and first_cons.hasServing()))
        )

        intro = "I finished my [first_cons.disp_name][first_cons_plur]."
        line_start = "I'm going to "

        if not get_more_first_cons:
            if first_cons_container_ref:
                line_mid = renpy.substitute("put this [first_cons_container_ref] away ")

            else:
                line_mid = renpy.substitute("put this away ")

        else:
            if first_cons_container_ref:
                line_mid = renpy.substitute("get another [first_cons_container_ref] ")

            elif first_cons_obj_ref:
                line_mid = renpy.substitute("get another [first_cons_obj_ref] ")

            else:
                more = "more" if first_cons_plur else "another one"
                line_mid = renpy.substitute("get [more] ")

        # This works for both paths above
        if second_cons_amount_ref is not None:
            some = second_cons_amount_ref + second_cons.disp_name + second_cons_plur
        else:
            some = mas_a_an_str(second_cons.disp_name) + second_cons_plur
        line_end = renpy.substitute("and make [some].")
    return

label mas_consumables_generic_finish_and_finishprep(first_cons, second_cons):
    python:
        # In case the acs wasn't updated, we do it here
        cons_done_acs = first_cons.acs_map[mas_consumables.CONS_DONE]
        if first_cons.acs is not cons_done_acs:
            monika_chr.remove_acs(first_cons.acs)
            first_cons.acs = cons_done_acs
            monika_chr.wear_acs(first_cons.acs)

        get_more_first_cons = (
            first_cons.shouldHave()
            and (first_cons.prepable() or (not first_cons.prepable() and first_cons.hasServing()))
        )

        is_are = "are" if plur else "is"
        intro = renpy.substitute("I finished my [first_cons.disp_name][first_cons_plur].")
        line_start = "I'm going to "

        if not get_more_first_cons:
            if first_cons_container_ref:
                line_mid = renpy.substitute("put this [first_cons_container_ref] away ")

            else:
                line_mid = renpy.substitute("put this away ")

            if second_cons_container_ref:
                line_end = renpy.substitute("and get [mas_a_an_str(second_cons_container_ref)] of [second_cons.disp_name][second_cons_plur].")

            elif second_cons_obj_ref:
                line_end = renpy.substitute("and get [mas_a_an_str(second_cons_obj_ref)] of [second_cons.disp_name][second_cons_plur].")

            else:
                a_an = (second_cons_amount_ref or "some") if (second_cons_plur or second_cons_amount_ref) else mas_a_an(second_cons.disp_name, ignore_case=True)
                line_end = renpy.substitute("and get [a_an] [second_cons.disp_name][second_cons_plur].")

        else:
            if first_cons_container_ref:
                line_mid = renpy.substitute("get another [first_cons_container_ref] ")

            elif first_cons_obj_ref:
                line_mid = renpy.substitute("get another [first_cons_obj_ref] ")

            else:
                more = "more" if (first_cons_plur or first_cons_amount_ref) else "another one"
                line_mid = renpy.substitute("get [more] ")

            if second_cons_container_ref:
                line_end = renpy.substitute("along with [mas_a_an_str(second_cons_container_ref)] of [second_cons.disp_name][second_cons_plur].")

            elif second_cons_obj_ref:
                line_end = renpy.substitute("along with [mas_a_an_str(second_cons_obj_ref)] of [second_cons.disp_name][second_cons_plur].")

            else:
                a_an = (second_cons_amount_ref or "some") if (second_cons_plur or second_cons_amount_ref) else mas_a_an(second_cons.disp_name, ignore_case=True)
                line_end = renpy.substitute("along with [a_an] [second_cons.disp_name][second_cons_plur].")
    return

#START: Generic consumable labels
label mas_consumables_generic_get(consumable):
    #Get our dlg_props
    python:
        dlg_props = consumable.ex_props

        container = dlg_props.get(mas_consumables.PROP_CONTAINER_REF)
        obj_ref = dlg_props.get(mas_consumables.PROP_OBJ_REF)
        plur = "s" if dlg_props.get(mas_consumables.PROP_PLUR, False) else ""

        #We need to parse the dialogue depending on the given dlg_props
        if container:
            line_starter = renpy.substitute("I'm going to get [mas_a_an_str(container)] of [consumable.disp_name][plur].")

        #Otherwise we use the object reference for this
        elif obj_ref:
            line_starter = renpy.substitute("I'm going to get [mas_a_an_str(obj_ref)] of [consumable.disp_name][plur].")

        #No valid dlg props
        else:
            a_an = "some" if plur else mas_a_an(consumable.disp_name, ignore_case=True)
            line_starter = renpy.substitute("I'm going to get [a_an] [consumable.disp_name][plur].")

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eua "[line_starter] I'll be right back.{w=1}{nw}"

    else:
        m 1eua "[line_starter]"
        m 1eua "Hold on a moment."

    #We want to take plush with
    if (
        consumable.consumable_type == store.mas_consumables.TYPE_FOOD
        and monika_chr.is_wearing_acs(mas_acs_quetzalplushie)
    ):
        $ mas_acs_quetzalplushie.keep_on_desk = False

    #Monika is off screen
    call mas_transition_to_emptydesk

    #Wrap these statements so we can properly add/remove the consumable
    python:
        renpy.pause(1.0, hard=True)
        consumable.acs.keep_on_desk = False
        monika_chr.remove_acs(mas_acs_quetzalplushie)
        monika_chr.wear_acs(consumable.acs)
        renpy.pause(4.0, hard=True)

    call mas_transition_from_emptydesk("monika 1eua")
    $ consumable.acs.keep_on_desk = True

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m 1eua "Okay, what else should we do today?"
    return

label mas_consumables_generic_finish_having(consumable):
    #Some prep
    python:
        # In case the acs wasn't updated, we do it here
        cons_done_acs = consumable.acs_map[mas_consumables.CONS_DONE]
        if consumable.acs is not cons_done_acs:
            monika_chr.remove_acs(consumable.acs)
            curr_cons.acs = cons_done_acs
            monika_chr.wear_acs(consumable.acs)

        get_more = (
            consumable.shouldHave()
            and (consumable.prepable() or (not consumable.prepable() and consumable.hasServing()))
        )

        dlg_props = consumable.ex_props

        container = dlg_props.get(mas_consumables.PROP_CONTAINER_REF)
        obj_ref = dlg_props.get(mas_consumables.PROP_OBJ_REF)
        plur = "s" if dlg_props.get(mas_consumables.PROP_PLUR, False) else ""

        dlg_map = {
            mas_consumables.PROP_CONTAINER_REF: {
                0: "I'm going to put this [container] away.",
                1: "I'm going to get another [container]."
            },
            mas_consumables.PROP_OBJ_REF: {
                0: "I'm going to put this away.",
                1: "I'm going to get another [obj_ref]."
            },
            "else": {
                0: "I'm going to put this away.",
                1: "I'm going to get another one."
            }
        }

        #We need to parse the dialogue depending on the given dlg_props
        if container:
            line_starter = renpy.substitute(dlg_map[mas_consumables.PROP_CONTAINER_REF][get_more])

        #Otherwise we use the object reference for this
        elif obj_ref:
            line_starter = renpy.substitute(dlg_map[mas_consumables.PROP_OBJ_REF][get_more])

        #No valid dlg props
        else:
            line_starter = renpy.substitute(dlg_map["else"][get_more])

    if (not mas_canCheckActiveWindow() or mas_isFocused()) and not store.mas_globals.in_idle_mode:
        m 1eud "I finished my [consumable.disp_name][plur].{w=0.2} {nw}"
        extend 1eua "[line_starter]"
        m 3eua "Hold on a moment."

    elif store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1esd "Oh, I've finished my [consumable.disp_name][plur].{w=1}{nw}"
        m 1eua "[line_starter] I'll be right back.{w=1}{nw}"

    #Monika is off screen
    $ consumable.acs.keep_on_desk = False
    call mas_transition_to_emptydesk

    #Wrap these statemetns so we can properly add / remove the acs
    python:
        renpy.pause(1.0, hard=True)

        #Should we get some more?
        if not get_more:
            #If not, we reset the current type's vars
            MASConsumable._reset(consumable.consumable_type)
            #And set up a time when we can have this drink again
            consumable.done_cons_until = datetime.datetime.now() + MASConsumable.DEF_DONE_CONS_TD

        else:
            consumable.have()
            consumable.re_serve()

            #Non-prepables are per refill, so they'll run out a bit faster
            if not consumable.prepable():
                consumable.use()

            #We still need to do this regarless (usually handled in use)
            else:
                consumable.last_had = datetime.datetime.now()
                consumable.acs = consumable.acs_map[mas_consumables.CONS_FULL]

        renpy.pause(4.0, hard=True)

    call mas_transition_from_emptydesk("monika 1eua")
    $ consumable.acs.keep_on_desk = True

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"
        #Let's queue this weekly if we've got something we're low on
        if (
            not mas_inEVL("mas_consumables_generic_queued_running_out")
            and mas_getEV("mas_consumables_generic_queued_running_out").timePassedSinceLastSeen_d(datetime.timedelta(days=7))
            and len(MASConsumable._getLowCons()) > 0
        ):
            $ mas_display_notif(m_name, ("Hey, [player]...",), "Topic Alerts")
            $ queueEvent("mas_consumables_generic_queued_running_out")

    #Only have one left
    elif not get_more and consumable.isCriticalLow() and consumable.should_restock_warn:
        call mas_consumables_generic_critical_low(consumable=consumable)

    #Running out
    elif not get_more and consumable.isLow() and consumable.should_restock_warn:
        call mas_consumables_generic_running_out(consumable=consumable)

    else:
        m 1eua "Okay, what else should we do today?"
    return

label mas_consumables_generic_finished_prepping(consumable):
    python:
        dlg_props = consumable.ex_props

        plur = "s" if dlg_props.get(mas_consumables.PROP_PLUR, False) else ""

    if (not mas_canCheckActiveWindow() or mas_isFocused()) and not store.mas_globals.in_idle_mode:
        $ is_are = "are" if plur else "is"
        m 1esd "Oh, my [consumable.disp_name][plur] [is_are] ready."
        m 1eua "Hold on a moment."

    else:
        #Idle pauses and then progresses on its own
        m 1eua "I'm going to get my [consumable.disp_name][plur]. I'll be right back.{w=1}{nw}"

    #Monika goes offscreen
    call mas_transition_to_emptydesk

    #Transition stuffs
    python:
        renpy.pause(1.0, hard=True)

        #Make sure drink is still gone
        consumable.acs.keep_on_desk = False
        #Now wear drink acs
        monika_chr.wear_acs(consumable.acs)

        #Reset prep time
        persistent._mas_current_consumable[consumable.consumable_type]["prep_time"] = None
        #Start drinking
        consumable.have()

        renpy.pause(4.0, hard=True)

    #And bring Moni back
    call mas_transition_from_emptydesk("monika 1eua")
    $ consumable.acs.keep_on_desk = True

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m 1eua "Okay, what else should we do today?"
    return

label mas_consumables_refill_explain:
    # provide in-universe explanation why Monika can't just dupe stuff, only shown once
    m 3rksdla "I'd duplicate what I have now...but when I tried before, it just wasn't the same..."
    m 1eksdla "I guess I must be missing something because I just can't seem to replicate the taste."
    if mas_isMoniHappy(higher=True):
        m 1ekbsu "...Or maybe it's your everlasting love that makes it special~"
    return

label mas_consumables_generic_running_out(consumable):
    $ amt_left = consumable.getStock()

    m 1euc "By the way, [player]..."

    if amt_left > 0:
        python:
            dlg_props = consumable.ex_props

            container = dlg_props.get(mas_consumables.PROP_CONTAINER_REF)
            obj_ref = dlg_props.get(mas_consumables.PROP_OBJ_REF)
            plur = "s" if dlg_props.get(mas_consumables.PROP_PLUR, False) else ""

            #We need to parse the dialogue depending on the given dlg_props
            if container:
                line_ender = renpy.substitute("[container]s of [consumable.disp_name][plur] left.")

            #Otherwise we use the object reference for this
            elif obj_ref:
                line_ender = renpy.substitute("[obj_ref]s of [consumable.disp_name][plur] left.")

            #No valid dlg props
            else:
                line_ender = renpy.substitute("[consumable.disp_name][plur] left.")

            if amt_left > 2:
                about = "about "

            else:
                about = ""

        m 3eud "I just wanted to let you know I only have [about][amt_left] [line_ender]"

        if not renpy.seen_label("mas_consumables_refill_explain"):
            call mas_consumables_refill_explain

    else:
        m 3eud "I just wanted to let you know that I'm out of [consumable.disp_name][plur]."

    m 1eka "You wouldn't mind getting some more for me, would you?"
    return

label mas_consumables_generic_critical_low(consumable):
    python:
        dlg_props = consumable.ex_props

        container = dlg_props.get(mas_consumables.PROP_CONTAINER_REF)
        obj_ref = dlg_props.get(mas_consumables.PROP_OBJ_REF)
        plur = "s" if dlg_props.get(mas_consumables.PROP_PLUR, False) else ""

        #We need to parse the dialogue depending on the given dlg_props
        if container:
            line_ender = renpy.substitute("[container] of [consumable.disp_name] left.")

        #Otherwise we use the object reference for this
        elif obj_ref:
            line_ender = renpy.substitute("[obj_ref] of [consumable.disp_name] left.")

        #No valid dlg props
        else:
            line_ender = renpy.substitute("serving of [consumable.disp_name] left.")

    m 1euc "Hey, [player]..."
    m 3eua "I only have one [line_ender]"

    if not renpy.seen_label("mas_consumables_refill_explain"):
        call mas_consumables_refill_explain

    m 3eka "Would you mind getting me some more sometime?"
    m 1hua "Thanks~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_consumables_generic_queued_running_out"
        )
    )

label mas_consumables_generic_queued_running_out:
    $ low_cons = MASConsumable._getLowCons()
    call mas_consumables_generic_queued_running_out_dlg(low_cons)
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_consumables_generic_running_out_absentuse"
        )
    )

label mas_consumables_generic_running_out_absentuse:
    $ low_cons = MASConsumable._getLowConsNotWarned()
    call mas_consumables_generic_queued_running_out_dlg(low_cons)
    return "no_unlock"


label mas_consumables_generic_queued_running_out_dlg(low_cons):
    # sanity check for non-empty list
    if not low_cons:
        return

    m 1esc "By the way, [player]..."
    if len(low_cons) > 2:
        $ mas_generateShoppingList(low_cons)
        m 3rksdla "I've been running out of a few things in here..."
        m 3eua "So I hope you don't mind, but I left you a list of things in the characters folder."
        $ them = "them"

    else:
        python:
            items_running_out_of = ""
            if len(low_cons) == 2:
                items_running_out_of = "{0} and {1}".format(low_cons[0].disp_name, low_cons[1].disp_name)
            else:
                items_running_out_of = low_cons[0].disp_name

        m 3rksdla "I'm running out of [items_running_out_of]."
        $ them = "some more"

    if not renpy.seen_label("mas_consumables_refill_explain"):
        call mas_consumables_refill_explain

    m 1eka "You wouldn't mind getting [them] for me, would you?"

    #Flag these as needing to be restocked
    python:
        for cons in low_cons:
            cons.flagRestockWarn()
    return

label mas_consumables_remove_thermos:
    #We just want to be able to push this directly
    if not monika_chr.is_wearing_acs_type("thermos-mug"):
        return

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eua "I'm going to put this thermos away. I'll be right back.{w=1}{nw}"

    else:
        m 1eua "Give me a second [player], I'm going to put this thermos away."

    $ thermos = monika_chr.get_acs_of_type("thermos-mug")
    window hide
    call mas_transition_to_emptydesk

    python:
        renpy.pause(3.0, hard=True)
        #Remove the current thermos
        monika_chr.remove_acs(thermos)
        renpy.pause(2.0, hard=True)

    call mas_transition_from_emptydesk("monika 1eua")
    window auto

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m "Okay, what else should we do today?"
    return

### Special labels for consumables
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_consumables_candycane_finish_having",
            show_in_idle=True,
            rules={"skip alert": None}
        ),
        restartBlacklist=True
    )

label mas_consumables_candycane_finish_having:
    #Some prep
    python:
        candycane = mas_getConsumable("candycane")
        candycane.acs.keep_on_desk = False
        get_more = candycane.shouldHave() and candycane.hasServing()

    if not get_more:
        # If we don't want more, then just clean things up
        python:
            #Reset the current type's vars
            MASConsumable._reset(candycane.consumable_type)
            candycane.acs.keep_on_desk = True
            #And set up a time when we can have this drink again
            candycane.done_cons_until = datetime.datetime.now() + MASConsumable.DEF_DONE_CONS_TD

    else:
        if not store.mas_globals.in_idle_mode and (not mas_canCheckActiveWindow() or mas_isFocused()):
            m 1eua "I'm going to get some more candy canes."
            m 3eua "Hold on a moment."

        elif store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
            m 1esd "Oh, I've eaten my candy canes.{w=1}{nw}"
            m 1eua "I'm going to get some more. I'll be right back.{w=1}{nw}"

        #Monika is off screen
        call mas_transition_to_emptydesk

        #Wrap these statemetns so we can properly add / remove the acs
        python:
            renpy.pause(1.0, hard=True)

            candycane.have()
            candycane.re_serve()
            #Non-prepables are per refill, so they'll run out a bit faster
            candycane.use()

            renpy.pause(4.0, hard=True)

        call mas_transition_from_emptydesk("monika 1eua")
        $ candycane.acs.keep_on_desk = True

        if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
            m 1hua "Back!{w=1.5}{nw}"
            #Let's queue this weekly if we've got something we're low on
            if (
                not mas_inEVL("mas_consumables_generic_queued_running_out")
                and mas_getEV("mas_consumables_generic_queued_running_out").timePassedSinceLastSeen_d(datetime.timedelta(days=7))
                and len(MASConsumable._getLowCons()) > 0
            ):
                $ queueEvent("mas_consumables_generic_queued_running_out")

        else:
            m 1eua "Okay, what else should we do today?"
    return
