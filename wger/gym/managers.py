# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import (
    Permission,
    User
)


class GymManager(models.Manager):
    '''
    Custom query manager for Gyms
    '''
    def get_members(self, gym_pk, activity_status):
        '''
        Returns all members for this gym (i.e non-admin ones)
        '''
        perm_gym = Permission.objects.get(codename='manage_gym')
        perm_gyms = Permission.objects.get(codename='manage_gyms')
        perm_trainer = Permission.objects.get(codename='gym_trainer')

        users = self.get_users_by_status(gym_pk, activity_status)
        return users.exclude(Q(groups__permissions=perm_gym) |
                             Q(groups__permissions=perm_gyms) |
                             Q(groups__permissions=perm_trainer)).distinct()

    def get_admins(self, gym_pk, activity_status):
        '''
        Returns all admins for this gym (i.e trainers, managers, etc.)
        '''
        perm_gym = Permission.objects.get(codename='manage_gym')
        perm_gyms = Permission.objects.get(codename='manage_gyms')
        perm_trainer = Permission.objects.get(codename='gym_trainer')

        users = self.get_users_by_status(gym_pk, activity_status)
        return users.filter(Q(groups__permissions=perm_gym) |
                            Q(groups__permissions=perm_gyms) |
                            Q(groups__permissions=perm_trainer)).distinct()


    def get_users_by_status(self, gym_pk, activity_status):
        '''
        Returns all users by activity status for a particular gym referenced by
        gym_pk
        '''
        if not activity_status or activity_status == 'active':
            users = User.objects.filter(userprofile__gym_id=gym_pk, is_active=True)
        elif activity_status == 'deactivated':
            users = User.objects.filter(userprofile__gym_id=gym_pk, is_active=False)

        return users
