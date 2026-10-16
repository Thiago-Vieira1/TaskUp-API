from rest_framework import serializers

from .models import Categoria, HistoricoTarefa, Notificacao, Subtarefa, Tarefa, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = "__all__"
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    nome = serializers.CharField()
    email = serializers.EmailField()


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class TarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarefa
        fields = "__all__"
        extra_kwargs = {
            "usuario": {
                "read_only": True
            }
        }


class SubtarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtarefa
        fields = "__all__"


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = "__all__"


class HistoricoTarefaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoTarefa
        fields = "__all__"
