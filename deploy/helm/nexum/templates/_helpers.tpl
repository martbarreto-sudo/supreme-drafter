{{/*
Nome base do chart (respeita nameOverride), truncado ao limite de DNS (63).
*/}}
{{- define "nexum.name" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Fullname: nome do release combinado com o nome do chart (respeita fullnameOverride).
*/}}
{{- define "nexum.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Identificador chart+versao para o label helm.sh/chart.
*/}}
{{- define "nexum.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Labels comuns aplicados a todos os recursos.
*/}}
{{- define "nexum.labels" -}}
helm.sh/chart: {{ include "nexum.chart" . }}
{{ include "nexum.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels base (nome + instancia). Componente adicionado pelos helpers
por-componente abaixo.
*/}}
{{- define "nexum.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nexum.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Labels/selector por componente. Recebe um dict { "context": ., "component": "..." }.
*/}}
{{- define "nexum.componentSelectorLabels" -}}
{{ include "nexum.selectorLabels" .context }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "nexum.componentLabels" -}}
{{ include "nexum.labels" .context }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/*
Atalhos por-componente (consumer/relay).
*/}}
{{- define "nexum.consumer.labels" -}}
{{ include "nexum.componentLabels" (dict "context" . "component" "consumer") }}
{{- end -}}
{{- define "nexum.consumer.selectorLabels" -}}
{{ include "nexum.componentSelectorLabels" (dict "context" . "component" "consumer") }}
{{- end -}}
{{- define "nexum.relay.labels" -}}
{{ include "nexum.componentLabels" (dict "context" . "component" "relay") }}
{{- end -}}
{{- define "nexum.relay.selectorLabels" -}}
{{ include "nexum.componentSelectorLabels" (dict "context" . "component" "relay") }}
{{- end -}}

{{/*
Nome do ServiceAccount a usar.
*/}}
{{- define "nexum.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "nexum.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
