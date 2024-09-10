from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username,email, phone=None,password=None, **extra_fields):

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            phone=phone,
            email=email,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.is_active = True
        user.email_verified=True
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username,password, **extra_fields):
        email = 'iamaparnasurendran@gmail.com'
        phone = extra_fields.get('phone','9497355185')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if password is None:
            raise ValueError('Superuser must have a password.')
        
        return self.create_user(username,email=email,password=password,phone=phone, **extra_fields)
