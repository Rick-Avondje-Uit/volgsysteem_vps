from django.urls import path
from core.views import activiteit, api, begeleider, core, deelnemer, deelnemer_instroom, deelnemer_portaal, doelen, methodiek, organisaties, rapportages, ticket, tickets_importeren, ticket_export,volgsysteem, volgsysteem_instellingen, vragenlijst
from core.views.deelnemer_email_lijst import deelnemer_email_lijst
from accounts.views.user_management import create_begeleider_and_send_email
from accounts.views.password_setup import set_username_password
from core.views.test_email import test_send_email
from core.views.weeztix import weeztix_redirect, weeztix_callback

app_name = "core"

urlpatterns = [
    path("", core.IndexView.as_view(), name='index'),

    # deelnemer gerelateerd
    path('rapportages/', deelnemer_portaal.RapportagesListView.as_view(), name='eigen_rapportages'),
    path('doelen/', deelnemer_portaal.DoelenListView.as_view(), name='eigen_doelen'),
    path("bewerk/", deelnemer_portaal.DeelnemerUpdateView.as_view(), name='update_gegevens'),

    # api gerelateerd
    path("api/deelnemers/", api.ApiDeelnemerList.as_view(), name='api_deelnemers'),
    path("api/begeleiders/", api.ApiBegeleiders.as_view(), name='api_begeleiders'),
    path("api/dagrapportages/", api.ApiRapportageList.as_view(), name='api_rapportage'),
    path("weeztix/connect/", weeztix_redirect, name="weeztix_redirect"),
    path("weeztix/callback/", weeztix_callback, name="weeztix_callback"),

    # begeleider gerelateerd
    path("activiteiten/", activiteit.ActiviteitListView.as_view(), name='activiteit_list'),
    path("activiteiten/<int:pk>/", activiteit.ActiviteitDetailView.as_view(), name='activiteit_detail'),
    path("activiteiten/<int:pk>/update/", activiteit.ActiviteitUpdateView.as_view(), name='activiteit_update'),
    path("activiteiten/<int:pk>/delete", activiteit.ActiviteitDeleteView.as_view(), name='activiteit_delete'),
    path("activiteiten/add/", activiteit.ActiviteitToevoegenView.as_view(), name='activiteit_add'),
    path("begeleiders/", begeleider.BegeleiderListView.as_view(), name='begeleider_list'),
    path("begeleiders/<int:pk>/update/", begeleider.BegeleiderUpdateView.as_view(), name='begeleider_update'),
    path("begeleiders/<int:pk>/delete/", begeleider.BegeleiderDeleteView.as_view(), name='begeleider_delete'),
    path("begeleiders/add/", begeleider.BegeleiderToevoegenView.as_view(), name='begeleider_add'),
    path("check_report_status/", ticket.CheckReportStatus.as_view(), name='check_status'),
    path('create_begeleider/', create_begeleider_and_send_email, name='create_begeleider'),
    path("deelnemers/", deelnemer.DeelnemerListView.as_view(), name='deelnemer_list'),
    path("deelnemers/zoek/", deelnemer.DeelnemerZoekView.as_view(), name='deelnemer_zoek'),
    path("deelnemers/add/", deelnemer.DeelnemerCreateView.as_view(), name='deelnemer_add'),
    path("deelnemers/emailadressen", deelnemer_email_lijst, name="deelnemer_email_lijst" ),
    path("deelnemers/<int:pk>/", deelnemer.DeelnemerDetailView.as_view(), name='deelnemer_detail'),
    path("deelnemers/<int:pk>/status/", volgsysteem.DeelnemerVolgsysteemDetailView.as_view(), name='deelnemer_volgsysteem_detail'),
    path('deelnemers/<int:pk>/delete/', deelnemer.DeelnemerDeleteView.as_view(), name='deelnemer_delete'),
    path('deelnemers/<int:pk>/update/', deelnemer.DeelnemerUpdateView.as_view(), name='deelnemer_update'),
    path('deelnemers/<int:pk>/update_instroom/', deelnemer.DeelnemerInstroomUpdateView.as_view(), name='deelnemer_update_instroom'),
    path('deelnemers/<int:pk>/create_uitstroom/', deelnemer.DeelnemerUitstroomCreateView.as_view(), name='deelnemer_create_uitstroom'),
    path('deelnemers/<int:pk>/delete_uitstroom/', deelnemer.DeelnemerUitstroomDeleteView.as_view(), name='deelnemer_delete_uitstroom'),
    path("deelnemers/<int:pk>/rapportages/", rapportages.RapportageListView.as_view(), name='rapportage_list'),
    path("deelnemers/<int:pk>/rapportages/add", rapportages.RapportageCreateView.as_view(), name='rapportage_add'),
    path('deelnemers/<int:pk>/doelen/', doelen.HoofdDoelListView.as_view(), name='deelnemer_doelen_list'),
    path('deelnemers/<int:pk>/doelen/add', doelen.HoofdDoelCreateView.as_view(), name='hoofddoel_add'),
    path("deelnemers/meedoen_regeling/", deelnemer.MeedoenRegelingListView.as_view(), name='deelnemer_meedoen_regeling'),
    path("deelnemers/volgsysteem/", volgsysteem.DeelnemerVolgsysteemListView.as_view(), name='deelnemer_volgsysteem_list'),
    path("deelnemers/<int:pk>/volgsysteem/update/", volgsysteem.DeelnemerVolgsysteemUpdateView.as_view(), name='deelnemer_volgsysteem_update'),
    path('deelnemers-api/', deelnemer.SuggestiesAPI.as_view(), name='suggesties_api'),
    path('deelnemers/naam_bestaat/', deelnemer.check_deelnemer, name='check_deelnemer'),
    path('doelen/<int:pk>/add', doelen.SubDoelCreateView.as_view(), name='subdoel_add'),
    path("doelen/<int:pk>/add_rapportage", rapportages.DoelRapportageCreateView.as_view(), name='add_rapportage_doel'),
    path("instellingen/", volgsysteem_instellingen.VolgsysteemInstellingenListView.as_view(), name='instellingen'),
    path("instellingen/<int:pk>/", volgsysteem_instellingen.VolgsysteemInstellingenDetailView.as_view(), name="instellingen_detail"),
    path("instroom/", deelnemer_instroom.DeelnemerInstroomPerMaand.as_view(), name='instroom_per_maand'),
    path("methodiek/", methodiek.MethodiekPuntenListView.as_view(), name='methodiek_list'),
    path("methodiek/<int:pk>/", methodiek.MethodiekPuntenDetailView.as_view(), name='methodiek_detail'),
    path("methodiek/<int:pk>/update/", methodiek.MethodiekPuntenUpdateView.as_view(), name='methodiek_update'),
    path("methodiek/<int:pk>/uitgevoerd/", methodiek.MethodiekPuntenActieUitgevoerd.as_view(), name='methodiek_uitgevoerd'),
    path("methodiek/add/", methodiek.MethodiekPuntenCreateView.as_view(), name='methodiek_add'),
    path("methodiek/check_duplicates/", methodiek.check_duplicates, name='check_duplicates_methodiek'),
    path("organisaties/", organisaties.OrganisatiesOverzichtView.as_view(), name='organisatie_list'),
    path("doel_rapportages/<int:pk>/update", rapportages.DoelRapportageUpdateView.as_view(), name='doel_rapportage_update'),
    path("doel_rapportages/<int:pk>/delete", rapportages.DoelRapportageDeleteView.as_view(), name='doel_rapportage_delete'),
    path("rapportages/<int:pk>/delete", rapportages.RapportageDeleteView.as_view(), name='rapportage_delete'),
    path("rapportages/<int:pk>/update", rapportages.RapportageUpdateView.as_view(), name='rapportage_update'),
    path("resultaten_vragenlijst/", vragenlijst.VragenlijstDeelnemersListView.as_view(), name='resultaten_vragenlijst_list'),
    path("resultaten_vragenlijst/ingevulde_lijsten/", vragenlijst.VragenlijstListView.as_view(), name='resultaten_vragenlijst_ingevuld'),
    path("resultaten_vragenlijst/<int:pk>/", vragenlijst.VragenlijstResultatenDeelnemerDetailView.as_view(), name='resultaten_vragenlijst_detail'),
    path("resultaten_vragenlijst/<int:pk>/update/", vragenlijst.VragenlijstDeelnemerUpdateView.as_view(), name='resultaten_vragenlijst_toekennen'),
    path('set_username_password/<uidb64>/<token>/', set_username_password, name='set_username_password'),
    path("subdoelen/<int:pk>/update", doelen.SubdoelUpdateView.as_view(), name='subdoel_update'),


   # admin gerelateerd
    path('weeztix/connect/', weeztix_redirect, name='weeztix_redirect'),
    path('weeztix/callback/', weeztix_callback, name='weeztix_callback'),
    path("tickets/", ticket.TicketListView.as_view(), name='ticket_list'),
    path("tickets/update/", tickets_importeren.SelectActiviteitenVoorTicketsView.as_view(), name='ticket_update'),
    path("tickets/laden/", ticket.TicketsLoading.as_view(), name="tickets_loading"),
    path("tickets/import/", tickets_importeren.DownloadTicketReport.as_view(), name='import_tickets'),
    path("tickets/toewijzen/", ticket.TicketsNogToeTeWijzenListView.as_view(), name='tickets_toewijzen'),
    path("tickets/download/", ticket_export.TicketExcelView.as_view(), name='download_tickets'),
    path("tickets/<int:pk>/update", ticket.TicketUpdateView.as_view(), name='ticket_update_individual'),
    path("tickets/<int:pk>/delete", ticket.TicketDeleteView.as_view(), name='ticket_delete'),
    path("test-email/",test_send_email, name='test_email'),
]
