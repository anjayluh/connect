from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from .models import ModerationLogMsg
from accounts.models import AbuseReport
from accounts.forms import validate_email_availability

User = get_user_model()


class InviteMemberForm(forms.Form):
    """
    Form for moderator to invite a new member.
    """
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    def clean(self):
        """
        Make sure email is not already in the system.
        """
        cleaned_data = super(InviteMemberForm, self).clean()
        email = cleaned_data.get('email')
        validate_email_availability(email)

        return cleaned_data


class ReInviteMemberForm(forms.Form):
    """
    Form for moderators to reinvite new users.
    Asks moderator to confirm they have sent the email to the correct address.
    """
    email = forms.EmailField()
    user_id = forms.IntegerField(widget=forms.HiddenInput)

    def clean(self):
        """
        If the moderator changes the email, make sure the new email is not already in the system.
        """
        cleaned_data = super(ReInviteMemberForm, self).clean()
        email = cleaned_data.get('email')
        user_id = cleaned_data.get('user_id')
        user = User.objects.get(id=user_id)

        # If this email is not already registered to this user
        if email != user.email:
            validate_email_availability(email)

        return cleaned_data


class RevokeMemberForm(forms.Form):
    """
    Form for moderator to revoke membership invitation.
    Requires moderator to confirm their action.
    """
    confirm = forms.BooleanField()
    user_id = forms.IntegerField(widget=forms.HiddenInput)


class ModerateApplicationForm(forms.Form):
    """
    Form for moderators to approve or reject an account application.
    """
    user_id = forms.IntegerField(widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=User.MODERATOR_CHOICES[1:],
                                 widget=forms.HiddenInput)
    comments = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Please explain your decision. '
                        'This information will not be sent to the user, '
                        'but will be recorded in the moderation logs.',
    }))


class ReportAbuseForm(forms.Form):
    """
    Form for a user to report abusive bahaviour of another user.
    """
    def __init__(self, *args, **kwargs):
        self.logged_by = kwargs.pop('logged_by', None)
        self.logged_against = kwargs.pop('logged_against', None)
        super(ReportAbuseForm, self).__init__(*args, **kwargs)

        self.fields['logged_by'] = forms.IntegerField(
                                                initial=self.logged_by.id,
                                                widget=forms.HiddenInput)

        self.fields['logged_against'] = forms.IntegerField(
                                                initial=self.logged_against.id,
                                                widget=forms.HiddenInput)

    comments = forms.CharField(widget=forms.Textarea())


class ModerateAbuseForm(forms.Form):
    """
    Form for a moderator to:
    - Dismiss an abuse report
    - Issue a warning
    - Remove abuser
    """
    report_id = forms.IntegerField(widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=AbuseReport.ABUSE_REPORT_CHOICES,
                                 widget=forms.HiddenInput)
    comments = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Please explain your decision. '
                        'This information will be sent to both users '
                        'and recorded in the moderation logs.',
    }))


class FilterLogsForm(forms.Form):
    """
    Form for a moderator to filter moderation logs by date, type and
    who the report has been logged against and logged by.
    """
    ALL = 'ALL'
    TODAY = 'TODAY'
    YESTERDAY = 'YESTERDAY'
    THIS_WEEK = 'THIS_WEEK'
    CUSTOM = 'CUSTOM'

    DATE_CHOICES = (
        (ALL, 'All'),
        (TODAY, 'Today'),
        (YESTERDAY, 'Yesterday'),
        (THIS_WEEK, 'This Week (Last 7 days)'),
        (CUSTOM, 'Custom Date Range'),
    )

    MSG_FILTER_CHOICES = ModerationLogMsg.MSG_TYPE_CHOICES
    MSG_FILTER_CHOICES.insert(0, (ALL, 'All'))

    msg_type = forms.ChoiceField(choices=MSG_FILTER_CHOICES,
                                 required=False)
    period = forms.ChoiceField(choices=DATE_CHOICES)

    start_date = forms.DateTimeField(required=False,
                            initial=lambda: date.today().replace(year=date.today().year - 1),
                            input_formats=('%d/%m/%Y',),
                            widget=forms.DateInput(
                                format='%d/%m/%Y',
                                attrs={
                                    'class': 'start-date',
                                    'placeholder': 'Start Date',
                                    #~# Disable by default (unless shown)
                                    'disabled': 'True',
                            }))

    end_date = forms.DateTimeField(required=False,
                        initial=date.today,
                        input_formats=('%d/%m/%Y',),
                        widget=forms.DateInput(
                            format='%d/%m/%Y',
                            attrs={
                                'class': 'end-date',
                                'placeholder': 'End Date',
                                # Disable by default (unless shown)
                                'disabled': 'True',
                        }))


    def clean(self):
        """
        If 'CUSTOM' is selected, check that both start_date and end_date
        have a value
        """
        cleaned_data = super(FilterLogsForm, self).clean()
        period = cleaned_data.get('period')

        if period == 'CUSTOM':

            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')

            if not start_date or not end_date:
                raise forms.ValidationError(
                    'To filter by date, please provide a start and end date',
                     code='missing_date')

        return cleaned_data
