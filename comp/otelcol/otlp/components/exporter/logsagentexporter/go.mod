module github.com/DataDog/datadog-agent/comp/otelcol/otlp/components/exporter/logsagentexporter

go 1.22.0

replace (
	github.com/DataDog/datadog-agent/comp/api/api/def => ../../../../../api/api/def
	github.com/DataDog/datadog-agent/comp/core/config => ../../../../../../comp/core/config
	github.com/DataDog/datadog-agent/comp/core/flare/builder => ../../../../../../comp/core/flare/builder
	github.com/DataDog/datadog-agent/comp/core/flare/types => ../../../../../../comp/core/flare/types
	github.com/DataDog/datadog-agent/comp/core/secrets => ../../../../../../comp/core/secrets
	github.com/DataDog/datadog-agent/comp/core/telemetry => ../../../../../../comp/core/telemetry
	github.com/DataDog/datadog-agent/comp/def => ../../../../../../comp/def
	github.com/DataDog/datadog-agent/comp/logs/agent/config => ../../../../../../comp/logs/agent/config
	github.com/DataDog/datadog-agent/comp/otelcol/otlp/testutil => ../../../../../../comp/otelcol/otlp/testutil
	github.com/DataDog/datadog-agent/pkg/collector/check/defaults => ../../../../../../pkg/collector/check/defaults
	github.com/DataDog/datadog-agent/pkg/config/env => ../../../../../../pkg/config/env
	github.com/DataDog/datadog-agent/pkg/config/mock => ../../../../../../pkg/config/mock
	github.com/DataDog/datadog-agent/pkg/config/model => ../../../../../../pkg/config/model
	github.com/DataDog/datadog-agent/pkg/config/setup => ../../../../../../pkg/config/setup
	github.com/DataDog/datadog-agent/pkg/config/structure => ../../../../../../pkg/config/structure
	github.com/DataDog/datadog-agent/pkg/config/utils => ../../../../../../pkg/config/utils
	github.com/DataDog/datadog-agent/pkg/logs/message => ../../../../../../pkg/logs/message
	github.com/DataDog/datadog-agent/pkg/logs/sources => ../../../../../../pkg/logs/sources
	github.com/DataDog/datadog-agent/pkg/logs/status/utils => ../../../../../../pkg/logs/status/utils
	github.com/DataDog/datadog-agent/pkg/proto => ../../../../../../pkg/proto
	github.com/DataDog/datadog-agent/pkg/telemetry => ../../../../../../pkg/telemetry
	github.com/DataDog/datadog-agent/pkg/util/executable => ../../../../../../pkg/util/executable
	github.com/DataDog/datadog-agent/pkg/util/filesystem => ../../../../../../pkg/util/filesystem
	github.com/DataDog/datadog-agent/pkg/util/fxutil => ../../../../../../pkg/util/fxutil
	github.com/DataDog/datadog-agent/pkg/util/hostname/validate => ../../../../../../pkg/util/hostname/validate
	github.com/DataDog/datadog-agent/pkg/util/log => ../../../../../../pkg/util/log
	github.com/DataDog/datadog-agent/pkg/util/optional => ../../../../../../pkg/util/optional
	github.com/DataDog/datadog-agent/pkg/util/pointer => ../../../../../../pkg/util/pointer
	github.com/DataDog/datadog-agent/pkg/util/scrubber => ../../../../../../pkg/util/scrubber
	github.com/DataDog/datadog-agent/pkg/util/statstracker => ../../../../../../pkg/util/statstracker
	github.com/DataDog/datadog-agent/pkg/util/system => ../../../../../../pkg/util/system
	github.com/DataDog/datadog-agent/pkg/util/system/socket => ../../../../../../pkg/util/system/socket
	github.com/DataDog/datadog-agent/pkg/util/testutil => ../../../../../../pkg/util/testutil
	github.com/DataDog/datadog-agent/pkg/util/winutil => ../../../../../../pkg/util/winutil
	github.com/DataDog/datadog-agent/pkg/version => ../../../../../../pkg/version
)

require (
	github.com/DataDog/datadog-agent/comp/logs/agent/config v0.56.0-rc.3
	github.com/DataDog/datadog-agent/comp/otelcol/otlp/testutil v0.56.0-rc.3
	github.com/DataDog/datadog-agent/pkg/logs/message v0.56.0-rc.3
	github.com/DataDog/datadog-agent/pkg/logs/sources v0.56.0-rc.3
	github.com/DataDog/datadog-agent/pkg/util/scrubber v0.57.0
	github.com/DataDog/opentelemetry-mapping-go/pkg/otlp/attributes v0.20.0
	github.com/DataDog/opentelemetry-mapping-go/pkg/otlp/logs v0.20.0
	github.com/stormcat24/protodep v0.1.8
	github.com/stretchr/testify v1.9.0
	go.opentelemetry.io/collector/component v0.104.0
	go.opentelemetry.io/collector/exporter v0.104.0
	go.opentelemetry.io/collector/pdata v1.11.0
)

require (
	github.com/DataDog/datadog-agent/comp/core/secrets v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/collector/check/defaults v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/config/env v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/config/model v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/config/setup v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/config/structure v0.0.0-00010101000000-000000000000 // indirect
	github.com/DataDog/datadog-agent/pkg/config/utils v0.56.0-rc.3 // indirect
	github.com/DataDog/datadog-agent/pkg/logs/status/utils v0.56.0-rc.3 // indirect
	github.com/DataDog/datadog-agent/pkg/proto v0.55.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/executable v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/filesystem v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/hostname/validate v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/log v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/optional v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/pointer v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/statstracker v0.56.0-rc.3 // indirect
	github.com/DataDog/datadog-agent/pkg/util/system v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/system/socket v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/util/winutil v0.57.0 // indirect
	github.com/DataDog/datadog-agent/pkg/version v0.56.0-rc.3 // indirect
	github.com/DataDog/datadog-api-client-go/v2 v2.13.0 // indirect
	github.com/DataDog/opentelemetry-mapping-go/pkg/inframetadata v0.20.0 // indirect
	github.com/DataDog/sketches-go v1.4.6 // indirect
	github.com/DataDog/viper v1.13.5 // indirect
	github.com/DataDog/zstd v1.5.2 // indirect
	github.com/Microsoft/go-winio v0.6.2 // indirect
	github.com/beorn7/perks v1.0.1 // indirect
	github.com/briandowns/spinner v1.23.0 // indirect
	github.com/cenkalti/backoff/v4 v4.3.0 // indirect
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/cihub/seelog v0.0.0-20170130134532-f561c5e57575 // indirect
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/fatih/color v1.15.0 // indirect
	github.com/fsnotify/fsnotify v1.7.0 // indirect
	github.com/go-logr/logr v1.4.1 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/go-ole/go-ole v1.2.6 // indirect
	github.com/go-viper/mapstructure/v2 v2.0.0-alpha.1 // indirect
	github.com/gogo/protobuf v1.3.2 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/hashicorp/go-version v1.7.0 // indirect
	github.com/hashicorp/hcl v1.0.0 // indirect
	github.com/hectane/go-acl v0.0.0-20190604041725-da78bae5fc95 // indirect
	github.com/json-iterator/go v1.1.12 // indirect
	github.com/kardianos/osext v0.0.0-20190222173326-2bc1f35cddc0 // indirect
	github.com/knadh/koanf/maps v0.1.1 // indirect
	github.com/knadh/koanf/providers/confmap v0.1.0 // indirect
	github.com/knadh/koanf/v2 v2.1.1 // indirect
	github.com/lufia/plan9stats v0.0.0-20220913051719-115f729f3c8c // indirect
	github.com/magiconair/properties v1.8.1 // indirect
	github.com/mattn/go-colorable v0.1.13 // indirect
	github.com/mattn/go-isatty v0.0.19 // indirect
	github.com/mitchellh/copystructure v1.2.0 // indirect
	github.com/mitchellh/mapstructure v1.5.1-0.20231216201459-8508981c8b6c // indirect
	github.com/mitchellh/reflectwalk v1.0.2 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/mohae/deepcopy v0.0.0-20170929034955-c48cc78d4826 // indirect
	github.com/pelletier/go-toml v1.9.5 // indirect
	github.com/philhofer/fwd v1.1.2 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	github.com/power-devops/perfstat v0.0.0-20220216144756-c35f1ee13d7c // indirect
	github.com/prometheus/client_golang v1.19.1 // indirect
	github.com/prometheus/client_model v0.6.1 // indirect
	github.com/prometheus/common v0.54.0 // indirect
	github.com/prometheus/procfs v0.15.1 // indirect
	github.com/rogpeppe/go-internal v1.12.0 // indirect
	github.com/shirou/gopsutil/v3 v3.24.4 // indirect
	github.com/shoenig/go-m1cpu v0.1.6 // indirect
	github.com/spf13/afero v1.1.2 // indirect
	github.com/spf13/cast v1.5.1 // indirect
	github.com/spf13/jwalterweatherman v1.0.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
	github.com/tinylib/msgp v1.1.8 // indirect
	github.com/tklauser/go-sysconf v0.3.12 // indirect
	github.com/tklauser/numcpus v0.6.1 // indirect
	github.com/yusufpapurcu/wmi v1.2.4 // indirect
	go.opentelemetry.io/collector v0.104.0 // indirect
	go.opentelemetry.io/collector/config/configretry v1.11.0 // indirect
	go.opentelemetry.io/collector/config/configtelemetry v0.104.0 // indirect
	go.opentelemetry.io/collector/confmap v0.104.0 // indirect
	go.opentelemetry.io/collector/consumer v0.104.0 // indirect
	go.opentelemetry.io/collector/extension v0.104.0 // indirect
	go.opentelemetry.io/collector/featuregate v1.11.0 // indirect
	go.opentelemetry.io/collector/receiver v0.104.0 // indirect
	go.opentelemetry.io/collector/semconv v0.104.0 // indirect
	go.opentelemetry.io/otel v1.27.0 // indirect
	go.opentelemetry.io/otel/exporters/prometheus v0.49.0 // indirect
	go.opentelemetry.io/otel/metric v1.27.0 // indirect
	go.opentelemetry.io/otel/sdk v1.27.0 // indirect
	go.opentelemetry.io/otel/sdk/metric v1.27.0 // indirect
	go.opentelemetry.io/otel/trace v1.27.0 // indirect
	go.uber.org/atomic v1.11.0 // indirect
	go.uber.org/multierr v1.11.0 // indirect
	go.uber.org/zap v1.27.0 // indirect
	golang.org/x/exp v0.0.0-20240808152545-0cdaa3abc0fa // indirect
	golang.org/x/net v0.28.0 // indirect
	golang.org/x/oauth2 v0.20.0 // indirect
	golang.org/x/sys v0.24.0 // indirect
	golang.org/x/term v0.23.0 // indirect
	golang.org/x/text v0.17.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240520151616-dc85e6b867a5 // indirect
	google.golang.org/grpc v1.64.0 // indirect
	google.golang.org/protobuf v1.34.2 // indirect
	gopkg.in/yaml.v2 v2.4.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)
