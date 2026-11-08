{{- define "sample-app.labels" -}}
app.kubernetes.io/part-of: sample-app
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "sample-app.podSecurity" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "sample-app.containerSecurity" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: [ALL]
{{- end -}}
