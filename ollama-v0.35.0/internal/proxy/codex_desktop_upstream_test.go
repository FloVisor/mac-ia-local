package proxy

import (
	"encoding/json"
	"testing"
)

func TestPrepareUpstreamRequestModelOverride(t *testing.T) {
	body := []byte(`{"model":"qwen36-omlx","input":[{"type":"message","role":"user","content":"hi"}]}`)
	got, err := prepareUpstreamRequest(body, routingModel{
		Slug:          "qwen36-omlx",
		UpstreamModel: "mlx-community--Qwen3.6-35B-A3B-4bit",
	})
	if err != nil {
		t.Fatal(err)
	}
	var payload map[string]json.RawMessage
	if err := json.Unmarshal(got, &payload); err != nil {
		t.Fatal(err)
	}
	var model string
	if err := json.Unmarshal(payload["model"], &model); err != nil {
		t.Fatal(err)
	}
	if model != "mlx-community--Qwen3.6-35B-A3B-4bit" {
		t.Fatalf("model not rewritten: %q", model)
	}
}

func TestPrepareUpstreamRequestEffortMapping(t *testing.T) {
	cases := []struct {
		effort        string
		wantThinking  bool
		wantBudget    int
		wantBudgetSet bool
	}{
		{"none", false, 0, false},
		{"low", true, 512, true},
		{"medium", true, 2048, true},
		{"high", true, 8192, true},
		{"max", true, 16384, true},
	}
	for _, tc := range cases {
		body := []byte(`{"model":"m","reasoning":{"effort":"` + tc.effort + `"},"input":[]}`)
		got, err := prepareUpstreamRequest(body, routingModel{Slug: "m"})
		if err != nil {
			t.Fatal(err)
		}
		var payload map[string]json.RawMessage
		if err := json.Unmarshal(got, &payload); err != nil {
			t.Fatal(err)
		}
		var ctk map[string]any
		if err := json.Unmarshal(payload["chat_template_kwargs"], &ctk); err != nil {
			t.Fatalf("%s: missing chat_template_kwargs", tc.effort)
		}
		if thinking, ok := ctk["enable_thinking"].(bool); !ok || thinking != tc.wantThinking {
			t.Fatalf("%s: enable_thinking = %v, want %v", tc.effort, ctk["enable_thinking"], tc.wantThinking)
		}
		rawBudget, hasBudget := payload["thinking_budget"]
		if hasBudget != tc.wantBudgetSet {
			t.Fatalf("%s: thinking_budget present = %v, want %v", tc.effort, hasBudget, tc.wantBudgetSet)
		}
		if hasBudget {
			var budget int
			if err := json.Unmarshal(rawBudget, &budget); err != nil || budget != tc.wantBudget {
				t.Fatalf("%s: thinking_budget = %d, want %d", tc.effort, budget, tc.wantBudget)
			}
		}
	}
}

func TestPrepareUpstreamRequestExplicitKwargsWin(t *testing.T) {
	body := []byte(`{"model":"m","reasoning":{"effort":"high"},"chat_template_kwargs":{"enable_thinking":false},"input":[]}`)
	got, err := prepareUpstreamRequest(body, routingModel{Slug: "m"})
	if err != nil {
		t.Fatal(err)
	}
	var payload map[string]json.RawMessage
	if err := json.Unmarshal(got, &payload); err != nil {
		t.Fatal(err)
	}
	var ctk map[string]any
	if err := json.Unmarshal(payload["chat_template_kwargs"], &ctk); err != nil {
		t.Fatal(err)
	}
	if thinking, ok := ctk["enable_thinking"].(bool); !ok || thinking {
		t.Fatal("explicit enable_thinking=false must not be overridden")
	}
	if _, hasBudget := payload["thinking_budget"]; hasBudget {
		t.Fatal("thinking_budget must not be set when thinking is explicitly disabled")
	}
}
