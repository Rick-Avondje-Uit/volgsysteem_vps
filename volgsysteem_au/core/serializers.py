from rest_framework import serializers
from .models import Begeleider, Deelnemer, DeelnemerInstroom, DeelnemerUitstroom, Plaats, DeelnemerMeedoenRegeling, DeelnemerVolgsysteem, DagRapportage

class BegeleiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Begeleider
        fields = '__all__'

class DeelnemerInstroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeelnemerInstroom
        fields = '__all__'

class DeelnemerUitstroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeelnemerUitstroom
        fields = '__all__'

class DeelnemerMeedoenRegelingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeelnemerMeedoenRegeling
        fields = '__all__'

class DeelnemerVolgsysteemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeelnemerVolgsysteem
        fields = '__all__'

class DeelnemerMeedoenregelingSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeelnemerMeedoenRegeling
        fields = '__all__'

class DeelnemerDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Deelnemer
        fields = '__all__'

class DeelnemerSerializer(serializers.ModelSerializer):
    deelnemer_instroom = DeelnemerInstroomSerializer()
    deelnemer_uitstroom = DeelnemerUitstroomSerializer()
    deelnemer_meedoeregeling = DeelnemerMeedoenRegelingSerializer()

    #tickets = serializers.StringRelatedField(many=True)
    class Meta:
        model = Deelnemer

        fields = ['naam', 'belangrijke_info', 'naam_tickets', 'geslacht', 'geboortedatum', 'woonplaats', 'aanmeld_locatie', 'zorgorganisatie', 
                'mobiele_nummer', 'email', 'deelnemer_instroom', 'deelnemer_uitstroom', 'deelnemer_meedoeregeling']


    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['geslacht'] = instance.get_geslacht_display()  # Overschrijft de originele waarde met de display value
        ret['aanmeld_locatie'] = instance.aanmeld_locatie.naam
        return ret

    def to_internal_value(self, data):
        # Zorg ervoor dat de interne waarde die opgeslagen moet worden correct wordt verwerkt
        for choice in Deelnemer.GESLACHT_CHOICES:
            if data.get('geslacht') == choice[1]:
                data['geslacht'] = choice[0]
                break
        data['aanmeld_locatie'] = Plaats.get(naam=data['aanmeld_locatie']).id
        return super().to_internal_value(data)

class RapportageSerializer(serializers.ModelSerializer):
    # voor post method om naam van deelnemer om te zetten naar id
    deelnemer_naam = serializers.CharField(write_only=True)
    # om id van deelnemer om te zetten naar naam bij get method
    naam_deelnemer = serializers.SerializerMethodField()
    class Meta:
        model = DagRapportage
        fields = ['deelnemer_naam', 'naam_deelnemer', 'datum', 'ingevuld_door', 'tekst']

    def get_naam_deelnemer(self, obj):
        return obj.deelnemer.naam 
    
    def create(self, validated_data):
        deelnemer_naam = validated_data.pop('deelnemer_naam')
        if not Deelnemer.objects.filter(naam=deelnemer_naam).exists():
            print(f"deelnemer: {deelnemer_naam} niet herkent")
            raise serializers.ValidationError({"deelnemer": f"{deelnemer_naam} niet herkent"}, 400)

        deelnemer = Deelnemer.objects.get(naam=deelnemer_naam)
        event, created = DagRapportage.objects.get_or_create(deelnemer=deelnemer, **validated_data)

        return event
    

class RapportageListSerializer(serializers.ListSerializer):
    child = RapportageSerializer()

    def create(self, validated_data):
        events = [self.child.create(attrs) for attrs in validated_data]
        return events
    
    def validate(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a list of items.")
        return data