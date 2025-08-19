from django.shortcuts import render , get_object_or_404 , redirect
from django.core.files.storage import FileSystemStorage
from .models import UploadedFile

from django.http import HttpResponse

def home(request): 
    uploaded_file_url= None
    if request.method == "POST" and request.FILES.get("uploaded_file"):
        uploaded_file = request.FILES["uploaded_file"]
        new_file = UploadedFile.objects.create(file=uploaded_file)        
        uploaded_file_url = new_file.file.url
        return redirect("chat", file_id=new_file.id)

    all_files = UploadedFile.objects.all().order_by('-uploaded_at')
        
    return render (request, 'home.html' , {"uploaded_file_url": uploaded_file_url, "all_files":all_files})


def chat_view(request, file_id):
    current_file = get_object_or_404(UploadedFile, id=file_id)
    other_files = UploadedFile.objects.exclude(id=file_id).order_by('-uploaded_at')

    return render(request, "chat.html", {
        "current_file": current_file,
        "other_files": other_files
    })