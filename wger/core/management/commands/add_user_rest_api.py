from django.core.management.base import BaseCommand, CommandError
from wger.core.models import UserProfile

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='+', type=str)

        parser.add_argument('--enabled',
                            action='store',
                            dest='enabled',
                            default=True,
                            help='Grant api consumers right to create users via REST API')

        parser.add_argument('--accounts-limit',
                            action='store',
                            dest='limit',
                            default=3,
                            help='Limits the number of accounts the API consumer can create per minute')

    def handle(self, *args, **options):
        username = options['username'][0]
        try:
            target_profile = UserProfile.objects.get(user__username=username)
        except UserProfile.DoesNotExist:
            raise CommandError('User profile for "%s" does not exist' % username)
        # update enabled using command options
        if options['enabled'] in (True, 'True', 'true', 'T', 't', '1', 1):
            enabled = True
        elif options['enabled'] in (False, 'False', 'false', 'F', 'f', '0', 0):
            enabled = False
        else:
            raise CommandError('Unknown value for option --enabled')

        if enabled:
            target_profile.api_add_user_enabled = True
            try:
                limit = int(options['limit'])
                target_profile.api_user_throughput_limit_per_min = limit
            except ValueError:
                raise CommandError('Invalid value for --accounts-limit option')

            target_profile.save()
            self.stdout.write(self.style.SUCCESS('Successfully ENABLED REST API user creation for "%s"' % username))
        else:
            target_profile.api_add_user_enabled = False
            target_profile.save()
            self.stdout.write(self.style.WARNING('Successfully DISABLED REST API user creation for "%s"' % username))
