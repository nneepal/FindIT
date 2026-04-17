from django import forms
from django.core.exceptions import ValidationError

from .models import ClaimVerification, FoundItem, LostItem


class FoundItemReportForm(forms.ModelForm):
    image = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={'class': 'file-input', 'id': 'file-upload', 'accept': '.jpg,.jpeg,.png,image/png,image/jpeg'}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [('', '---'), *self.fields['category'].choices]
        self.fields['location_found'].choices = [('', '---'), *self.fields['location_found'].choices]
        self.fields['condition'].choices = [('', '---'), *self.fields['condition'].choices]

    class Meta:
        model = FoundItem
        fields = [
            'item_name',
            'category',
            'location_found',
            'date_found',
            'condition',
            'is_valuable',
            'description',
            'image',
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location_found': forms.Select(attrs={'class': 'form-select with-icon'}),
            'date_found': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'is_valuable': forms.RadioSelect(
                choices=[(True, 'Yes'), (False, 'No')],
                attrs={'class': 'radio-input'},
            ),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'image': forms.ClearableFileInput(
                attrs={'class': 'file-input', 'id': 'file-upload', 'accept': '.jpg,.jpeg,.png,image/png,image/jpeg'}
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise ValidationError('Please upload an image.')

        max_size = 5 * 1024 * 1024
        if image.size > max_size:
            raise ValidationError('Image size must be less than 5MB.')

        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        filename = image.name.lower()
        if not any(filename.endswith(extension) for extension in allowed_extensions):
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        content_type = getattr(image, 'content_type', '')
        if content_type not in {'image/jpeg', 'image/png'}:
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        return image


class LostItemSearchForm(forms.ModelForm):
    image = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={'class': 'file-input', 'id': 'search-file-upload', 'accept': '.jpg,.jpeg,.png,image/png,image/jpeg'}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = [('', '---'), *self.fields['category'].choices]
        self.fields['condition'].choices = [('', '---'), *self.fields['condition'].choices]
        self.fields['location_lost'].choices = [('', '---'), *self.fields['location_lost'].choices]

    class Meta:
        model = LostItem
        fields = [
            'item_name',
            'category',
            'condition',
            'location_lost',
            'date_lost',
            'description',
            'image',
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'location_lost': forms.Select(attrs={'class': 'form-select with-icon'}),
            'date_lost': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'image': forms.ClearableFileInput(
                attrs={'class': 'file-input', 'id': 'search-file-upload', 'accept': '.jpg,.jpeg,.png,image/png,image/jpeg'}
            ),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise ValidationError('Please upload an image.')

        max_size = 5 * 1024 * 1024
        if image.size > max_size:
            raise ValidationError('Image size must be less than 5MB.')

        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        filename = image.name.lower()
        if not any(filename.endswith(extension) for extension in allowed_extensions):
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        content_type = getattr(image, 'content_type', '')
        if content_type not in {'image/jpeg', 'image/png'}:
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        return image


class ClaimVerificationForm(forms.ModelForm):
    proof_image = forms.FileField(required=False)

    class Meta:
        model = ClaimVerification
        fields = ['description', 'proof_image']
        widgets = {
            'description': forms.Textarea(
                attrs={
                    'class': 'verification-textarea',
                    'placeholder': 'Explain clearly why this item belongs to you. Mention any unique marks or details.',
                    'rows': 6,
                }
            ),
            'proof_image': forms.ClearableFileInput(
                attrs={'class': 'verification-file-input', 'accept': '.jpg,.jpeg,.png,image/png,image/jpeg'}
            ),
        }

    def clean_proof_image(self):
        proof_image = self.cleaned_data.get('proof_image')
        if not proof_image:
            return proof_image

        max_size = 5 * 1024 * 1024
        if proof_image.size > max_size:
            raise ValidationError('Image size must be less than 5MB.')

        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        filename = proof_image.name.lower()
        if not any(filename.endswith(extension) for extension in allowed_extensions):
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        content_type = getattr(proof_image, 'content_type', '')
        if content_type and content_type not in {'image/jpeg', 'image/png'}:
            raise ValidationError('Only JPG, JPEG, or PNG files are allowed.')

        return proof_image