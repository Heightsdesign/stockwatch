# alerts/views.py
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, filters, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .models import (
    Stock,
    Alert,
    PriceTargetAlert,
    PercentageChangeAlert,
    Indicator,
    IndicatorLine,
    IndicatorChainAlert,
)
from .serializers import (
    StockSerializer,
    AlertSerializer,
    PriceTargetAlertSerializer,
    PercentageChangeAlertSerializer,
    IndicatorChainAlertSerializer,
    IndicatorSerializer,
    IndicatorLineSerializer
)


class StockListView(generics.ListAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['symbol', 'name']


# 2. View to retrieve stock details
class StockDetailView(generics.RetrieveAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'symbol'


# 3. View to retrieve user's alerts
class UserAlertsView(generics.ListAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)


# 4. ViewSets for alert creation and management
class PriceTargetAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceTargetAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PriceTargetAlert.objects.filter(alert__user=self.request.user)


class PercentageChangeAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PercentageChangeAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PercentageChangeAlert.objects.filter(alert__user=self.request.user)

class IndicatorChainAlertViewSet(viewsets.ModelViewSet):
    serializer_class = IndicatorChainAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IndicatorChainAlert.objects.filter(alert__user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Ensure the request is passed to the serializer context
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return the serialized data
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Indicator.objects.all()
    serializer_class = IndicatorSerializer
    permission_classes = [AllowAny]


class IndicatorLineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndicatorLine.objects.all()
    serializer_class = IndicatorLineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        indicator_id = self.request.query_params.get('indicator_id')
        if indicator_id:
            return self.queryset.filter(indicators__id=indicator_id)
        return self.queryset


class UserAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        alert = self.get_object()
        data = request.data

        # Update the main Alert fields
        serializer = self.get_serializer(alert, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Update related alert details
        if alert.alert_type == 'PRICE':
            price_alert = alert.price_target_alert
            price_serializer = PriceTargetAlertSerializer(
                price_alert,
                data=data,
                partial=True,
                context={'request': request}
            )
            price_serializer.is_valid(raise_exception=True)
            price_serializer.save()
        elif alert.alert_type == 'PERCENT_CHANGE':
            percent_alert = alert.percentage_change
            percent_serializer = PercentageChangeAlertSerializer(
                percent_alert,
                data=data,
                partial=True,
                context={'request': request}
            )
            percent_serializer.is_valid(raise_exception=True)
            percent_serializer.save()
        elif alert.alert_type == 'INDICATOR_CHAIN':
            indicator_chain_alert = alert.indicator_chain
            indicator_chain_serializer = IndicatorChainAlertSerializer(
                indicator_chain_alert,
                data=data,
                partial=True,
                context={'request': request}
            )
            indicator_chain_serializer.is_valid(raise_exception=True)
            indicator_chain_serializer.save()
        # Handle other alert types similarly

        return Response(serializer.data)

