from django.urls import path
from . import views

urlpatterns = [
    path('criar-caso/', views.criar_caso_view, name='criar_caso'),
    path('editar-laudo/<str:caso_id>/', views.editar_laudo_view, name='editar_laudo'),
    path('caso/<str:caso_id>/macro/solicitar/', views.solicitar_macro_aprovacao_view, name='solicitar_macro_aprovacao'),
    path('caso/<str:caso_id>/macro/aprovar/', views.aprovar_macroscopia_view, name='aprovar_macroscopia'),
    path('caso/<str:caso_id>/preparo/solicitar/', views.solicitar_preparo_aprovacao_view, name='solicitar_preparo_aprovacao'),
    path('caso/<str:caso_id>/preparo/aprovar/', views.aprovar_preparo_view, name='aprovar_preparo'),
    path('caso/<str:caso_id>/micro/solicitar/', views.solicitar_microscopia_aprovacao_view, name='solicitar_microscopia_aprovacao'),
    path('caso/<str:caso_id>/micro/aprovar/', views.aprovar_microscopia_view, name='aprovar_microscopia'),
    path('aprovar-laudo/<str:caso_id>/', views.aprovar_laudo_view, name='aprovar_laudo'),
    path('laudo-macro/<str:caso_id>/', views.laudo_macro_view, name='laudo_macro'),
    path('laudo-micro/<str:caso_id>/', views.laudo_micro_view, name='laudo_micro'),
    path('pdf/<str:caso_id>/', views.gerar_pdf_view, name='gerar_pdf'),
]
