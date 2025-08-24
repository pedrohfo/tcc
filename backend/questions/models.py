from django.db import models

class Test(models.Model):
    name = models.TextField(unique=True)

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question_number = models.IntegerField()
    subject = models.TextField()
    question_text = models.TextField()
    image = models.ImageField(upload_to="questions/", null=True, blank=True)

class Alternative(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    alternative_text = models.TextField()
    alternative_number = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
