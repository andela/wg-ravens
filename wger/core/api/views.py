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
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
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
            api_user = User.objects.filter(id=token.user_id).first()
            users = User.objects.filter(userprofile__gym_id = api_user.userprofile.gym_id)
        return users

    def create(self, request):
        token = self.fetch_api_token_object()
        if not token:
            msg = 'API Authorization data required'
            response = self.make_response_message(message=msg, status=403)
            return response

        api_user = User.objects.filter(id=token.user_id).first()
        if not api_user:
            msg = 'Invalid API Authorization data'
            response = self.make_response_message(message=msg, status=403)
            return response

        username = request.data.get('username')
        password = request.data.get('password')
        roles = request.data.get('roles')
        # create a new user
        try:
            new_user = User(username=username, password=password)
            new_user.save()
        except IntegrityError as err:
            msg = 'Username already exists'
            response = self.make_response_message(message=msg, status=409)
            return response


        new_user.userprofile.gym_id = api_user.userprofile.gym_id
        new_user.userprofile.created_by = token
        new_user.userprofile.save()

        msg = 'User successfully registered'
        response = self.make_response_message(message=msg)
        return response

    def fetch_api_token_object(self):
        api_key = self.request.META.get('HTTP_AUTHORIZATION')
        if not api_key:
            return None
        api_key = api_key.split()[1]
        token = Token.objects.filter(key=api_key).first()
        return token

    def make_response_message(self, message, status=200):
        msg = json.dumps({
            "message": message
        })
        response = HttpResponse(msg, status=status)
        response['content-type'] = 'application/json'
        return response


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
