# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import UploadedFile , ChatHistory
from .rag_pipeline import process_file_with_rag, ask_gemini
from allauth.account.views import LogoutView as AllauthLogoutView


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
    if request.method == "POST":
        query = request.POST.get("query")
        answer = ask_gemini(query, file_id)

        # Save history if user is logged in
        if request.user.is_authenticated:
            ChatHistory.objects.create(
                user=request.user,
                file_id=file_id,
                query=query,
                answer=answer
            )

        return JsonResponse({"answer": answer})

    current_file = get_object_or_404(UploadedFile, id=file_id)

    # Show only files that the current user has chat history with
    if request.user.is_authenticated:
        # Get file IDs from ChatHistory for this user
        file_ids = ChatHistory.objects.filter(user=request.user).values_list('file_id', flat=True).distinct()
        other_files = UploadedFile.objects.filter(id__in=file_ids).exclude(id=file_id).order_by('-uploaded_at')
    else:
        # If not logged in, show empty list
        other_files = UploadedFile.objects.none()

    # Get user's chat history for the current file
    user_history = ChatHistory.objects.filter(user=request.user, file=current_file) if request.user.is_authenticated else []

    return render(request, "chat.html", {
        "current_file": current_file,
        "other_files": other_files,
        "chat_history": user_history
    })

    

class CustomLogoutView(AllauthLogoutView):
    template_name = 'account/logout.html'