# alerts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StockListView,
    StockDetailView,
    UserAlertsView,
    PriceTargetAlertViewSet,
    PercentageChangeAlertViewSet,
    IndicatorChainAlertViewSet,
    UserAlertDetailView,
    IndicatorDefinitionListView,  # Added this import
    # Removed IndicatorViewSet and IndicatorLineViewSet
)

router = DefaultRouter()
router.register(r'price-target-alerts', PriceTargetAlertViewSet, basename='price-target-alert')
router.register(r'percentage-change-alerts', PercentageChangeAlertViewSet, basename='percentage-change-alert')
router.register(r'indicator-chain-alerts', IndicatorChainAlertViewSet, basename='indicator-chain-alert')
# Removed router registrations for 'indicators' and 'indicator-lines'

urlpatterns = [
    path('', include(router.urls)),
    path('stocks/', StockListView.as_view(), name='stock-list'),
    path('stocks/<str:symbol>/', StockDetailView.as_view(), name='stock-detail'),
    path('user-alerts/', UserAlertsView.as_view(), name='user-alerts'),
    path('alerts/<int:pk>/', UserAlertDetailView.as_view(), name='alert-detail'),
    path('indicators/', IndicatorDefinitionListView.as_view(), name='indicator-list'),  # Added this URL pattern
]
