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
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

import json

from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError
from django.db.models import F
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.authtoken.models import Token

from wger.core.models import (
    UserProfile,
    Language,
    DaysOfWeek,
    License,
    RepetitionUnit,
    WeightUnit)
from wger.core.api.serializers import (
    UsernameSerializer,
    LanguageSerializer,
    DaysOfWeekSerializer,
    LicenseSerializer,
    RepetitionUnitSerializer,
    WeightUnitSerializer,
    UserSerializer
)
from wger.core.api.serializers import UserprofileSerializer
from wger.utils.permissions import UpdateOnlyPermission, WgerPermission

class UserViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for creating users and listing users
    '''
    serializer_class = UserSerializer

    def get_queryset(self):
        '''
        Only allow access to users created with an API's Key
        '''
        users = []
        token = self.fetch_api_token_object()

        if token:
            users = User.objects.filter(userprofile__created_by=token.key)
        return users


    def create(self, request):
        '''
        Attempts to create a user via ReST API
        '''
        api_user = request.user
        token = self.fetch_api_token_object()
        result = self.validate_user_api_conditions(token, api_user)
        # returns an error HttpResponse object if any condition fails
        if isinstance(result, HttpResponse):
            return result

        # create the user
        user_data = self.serializer_class().extract_valid_fields(request.data)
        ## persist user
        try:
            new_user = User.objects.create_user(**user_data)
            new_user.save()
        except IntegrityError:
            msg = 'Username already exists'
            return self.make_response_message(message=msg, status=409)

        # add user to groups specified in request data
        roles = request.data.get('roles')
        self.add_user_roles(user=new_user, roles=roles)

        # add user to api_user's gym
        new_user.userprofile.gym_id = api_user.userprofile.gym_id
        new_user.userprofile.created_by = token
        new_user.userprofile.save()

        ## user creation successful: update throughput details
        api_user.userprofile.api_user_count_this_cycle = F('api_user_count_this_cycle') + 1
        api_user.userprofile.save()

        msg = 'User successfully registered'
        return self.make_response_message(message=msg)


    def validate_user_api_conditions(self, token, api_user=None):
        '''
        Verifies that all conditions for using the ReST API to create users are
        fulfilled. Returns an error HttpResponse object if unsuccessful or the
        API key bearer if all well
        '''
        # Check if api_user has right to add users via API
        if not api_user.userprofile.api_add_user_enabled:
            msg = 'Please request wger admin for API user creation rights'
            return self.make_response_message(message=msg, status=403)

        # check if api user within API user creation limit
        user_within_threshold = self.check_api_throughput(api_user)
        if not user_within_threshold:
            msg = 'You have reached your API limit. Wait for at most 1 minute.'
            return self.make_response_message(message=msg, status=403)


    def check_api_throughput(self, user):
        '''
        Checks if a user has surpassed the limit of user accounts they can
        create per minute. A simple protection against third-party applications
        flooding database with user accounts
        '''
        max_accounts = user.userprofile.api_user_throughput_limit_per_min
        accounts_created = user.userprofile.api_user_count_this_cycle
        cycle_start_time = user.userprofile.api_throughput_cycle_begin_time
        time_diff_sec =  (timezone.now() - cycle_start_time).seconds

        if accounts_created >= max_accounts and time_diff_sec < 60:
            return False

        if time_diff_sec >= 60:
            # reset cycle
            user.userprofile.api_throughput_cycle_begin_time = timezone.now()
            user.userprofile.api_user_count_this_cycle = 0
            user.userprofile.save()
        return True


    def fetch_api_token_object(self):
        '''
        Extracts API key from request headers and gets a ReST API Token object
        from the database
        '''
        api_key = self.request.auth
        if not api_key:
            return None
        token = Token.objects.filter(key=api_key).first()
        return token


    def make_response_message(self, message, status=200):
        '''
        For making JSON responses
        '''
        msg = json.dumps({
            "detail": message
        })
        response = HttpResponse(msg, status=status)
        response['content-type'] = 'application/json'
        return response


    def add_user_roles(self, user, roles):
        '''
        Adds new user to groups specified by roles in incoming POST data
        '''
        # default role
        if len(roles) == 0:
            roles = ['gym_member']

        for name in roles:
            group = Group.objects.filter(name=name).first()
            if not group:
                continue
            user.groups.add(group)



class UserProfileViewSet(viewsets.ModelViewSet):
    '''
    API endpoint for workout objects
    '''
    is_private = True
    serializer_class = UserprofileSerializer
    permission_classes = (WgerPermission, UpdateOnlyPermission)
    ordering_fields = '__all__'

    def get_queryset(self):
        '''
        Only allow access to appropriate objects
        '''
        return UserProfile.objects.filter(user=self.request.user)

    def get_owner_objects(self):
        '''
        Return objects to check for ownership permission
        '''
        return [(User, 'user')]

    @detail_route()
    def username(self, request, pk):
        '''
        Return the username
        '''

        user = self.get_object().user
        return Response(UsernameSerializer(user).data)


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    ordering_fields = '__all__'
    filter_fields = ('full_name',
                     'short_name')


class DaysOfWeekViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = DaysOfWeek.objects.all()
    serializer_class = DaysOfWeekSerializer
    ordering_fields = '__all__'
    filter_fields = ('day_of_week', )


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for workout objects
    '''
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    ordering_fields = '__all__'
    filter_fields = ('full_name',
                     'short_name',
                     'url')


class RepetitionUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for repetition units objects
    '''
    queryset = RepetitionUnit.objects.all()
    serializer_class = RepetitionUnitSerializer
    ordering_fields = '__all__'
    filter_fields = ('name', )


class WeightUnitViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint for weight units objects
    '''
    queryset = WeightUnit.objects.all()
    serializer_class = WeightUnitSerializer
    ordering_fields = '__all__'
    filter_fields = ('name', )
