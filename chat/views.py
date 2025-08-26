from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import UploadedFile, ChatHistory
from allauth.account.views import LogoutView as AllauthLogoutView
import os
from huggingface_hub import hf_hub_download
import importlib.util

CACHE_DIR = os.path.join(os.path.dirname(__file__), "hf_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Download & load pipeline
rag_file_path = hf_hub_download(
    repo_id="VivanRajath/RAG_BOT",
    filename="rag_pipeline.py",
    cache_dir=CACHE_DIR
)
spec = importlib.util.spec_from_file_location("rag_pipeline", rag_file_path)
rag_pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rag_pipeline)

process_file_with_rag = rag_pipeline.process_file_with_rag
ask_gemini = rag_pipeline.ask_gemini

def home(request):
    uploaded_file_url = None
    if request.method == "POST" and request.FILES.get("uploaded_file"):
        uploaded_file = request.FILES["uploaded_file"]
        new_file = UploadedFile.objects.create(file=uploaded_file)
        uploaded_file_url = new_file.file.url
        process_file_with_rag(new_file.file.path, new_file.id)
        return redirect("chat", file_id=new_file.id)

    all_files = UploadedFile.objects.all().order_by('-uploaded_at')
    return render(request, 'home.html', {
        "uploaded_file_url": uploaded_file_url,
        "all_files": all_files
    })

def chat_view(request, file_id):
    current_file = get_object_or_404(UploadedFile, id=file_id)

    if request.method == "POST":
        query = request.POST.get("query")
        answer = ask_gemini(query, file_id)
        if request.user.is_authenticated:
            ChatHistory.objects.create(
                user=request.user,
                file_id=file_id,
                query=query,
                answer=answer
            )
        return JsonResponse({"answer": answer})

    if request.user.is_authenticated:
        file_ids = ChatHistory.objects.filter(user=request.user).values_list('file_id', flat=True).distinct()
        other_files = UploadedFile.objects.filter(id__in=file_ids).exclude(id=file_id).order_by('-uploaded_at')
        user_history = ChatHistory.objects.filter(user=request.user, file=current_file)
    else:
        other_files = UploadedFile.objects.none()
        user_history = []

    return render(request, "chat.html", {
        "current_file": current_file,
        "other_files": other_files,
        "chat_history": user_history
    })

class CustomLogoutView(AllauthLogoutView):
    template_name = 'account/logout.html'
