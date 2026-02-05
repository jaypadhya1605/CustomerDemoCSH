import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
import json

# CRITICAL: Set environment variable BEFORE any instrumentation
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

# Initialize OpenAI instrumentation for tracing
OpenAIInstrumentor().instrument()

# Initialize Azure AI Project Client with Entra ID
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://aif-eastus2-customerdemo-jp-demo-001.services.ai.azure.com/api/projects/aif_project_001"
)

# Configure Azure Monitor for tracing
try:
    connection_string = project.telemetry.get_application_insights_connection_string()
    print(f"Application Insights Connection String: {connection_string}")
    configure_azure_monitor(connection_string=connection_string)
    print("✅ Tracing configured successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not configure tracing: {e}")

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

def run_agent_conversation_with_tracing(agent_id: str, user_message: str, conversation_name: str = "agent_conversation"):
    """
    Run an agent conversation with full tracing capabilities including input/output capture
    
    Args:
        agent_id: The ID of your Azure AI agent
        user_message: The message to send to the agent
        conversation_name: Name for the trace span (optional)
    """
    
    # Create a custom span to group all agent operations
    with tracer.start_as_current_span(conversation_name) as span:
        try:
            print(f"🤖 Starting conversation with agent: {agent_id}")
            
            # Get the agent
            agent = project.agents.get_agent(agent_id)
            agent_name = agent.name if hasattr(agent, 'name') else 'Unknown'
            print(f"✅ Agent retrieved: {agent_name}")
            
            # Create a new thread for this conversation
            thread = project.agents.threads.create()
            print(f"✅ Created thread, ID: {thread.id}")
            
            # Send user message to the thread
            message = project.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            print(f"✅ User message sent: {user_message}")
            
            # Create and process the run
            print("🔄 Processing agent response...")
            run = project.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Check run status
            if run.status == "failed":
                error_msg = f"Run failed: {run.last_error}"
                print(f"❌ {error_msg}")
                span.set_status(Status(StatusCode.ERROR, error_msg))
                return None
            else:
                print(f"✅ Run completed successfully with status: {run.status}")
            
            # Retrieve all messages in the conversation
            messages = project.agents.messages.list(
                thread_id=thread.id, 
                order=ListSortOrder.ASCENDING
            )
            
            print("\n🗨️ Conversation History:")
            print("-" * 50)
            
            conversation_history = []
            user_input = ""
            assistant_output = ""
            
            for message in messages:
                if message.text_messages:
                    message_content = message.text_messages[-1].text.value
                    print(f"{message.role.upper()}: {message_content}")
                    conversation_history.append({
                        "role": message.role,
                        "content": message_content
                    })
                    
                    # Capture input and output for tracing
                    if message.role == "user":
                        user_input = message_content
                    elif message.role == "assistant":
                        assistant_output = message_content
            
            # CRITICAL: Manually add input/output as span events to make them visible in tracing
            # This is what makes the Input/Output columns populate in Azure AI Foundry
            if user_input:
                span.add_event(
                    name="gen_ai.content.prompt",
                    attributes={
                        "gen_ai.prompt": user_input,
                        "gen_ai.system": "azure_ai_agents"
                    }
                )
                # Also set as regular attributes
                span.set_attribute("gen_ai.prompt", user_input)
                span.set_attribute("user.input", user_input)
            
            if assistant_output:
                span.add_event(
                    name="gen_ai.content.completion",
                    attributes={
                        "gen_ai.completion": assistant_output,
                        "gen_ai.system": "azure_ai_agents"
                    }
                )
                # Also set as regular attributes
                span.set_attribute("gen_ai.completion", assistant_output)
                span.set_attribute("assistant.output", assistant_output)
            
            # Add comprehensive span attributes for better tracking
            span.set_attribute("agent_id", agent_id)
            span.set_attribute("agent_name", agent_name)
            span.set_attribute("thread_id", thread.id)
            span.set_attribute("run_id", run.id)
            span.set_attribute("run_status", run.status)
            span.set_attribute("conversation_length", len(conversation_history))
            span.set_attribute("gen_ai.system", "azure_ai_agents")
            span.set_attribute("gen_ai.request.model", agent_id)
            
            # Add the full conversation as a JSON attribute
            span.set_attribute("conversation_history", json.dumps(conversation_history))
            
            print("-" * 50)
            print("✅ Conversation completed and traced with input/output!")
            
            return {
                "thread_id": thread.id,
                "run_id": run.id,
                "run_status": run.status,
                "conversation": conversation_history,
                "user_input": user_input,
                "assistant_output": assistant_output
            }
            
        except Exception as e:
            error_msg = f"Error in agent conversation: {str(e)}"
            print(f"❌ {error_msg}")
            span.set_status(Status(StatusCode.ERROR, error_msg))
            raise e

def run_direct_openai_call_for_comparison():
    """
    Run a direct OpenAI call to show the difference in tracing
    This will automatically get input/output captured by the OpenAI instrumentor
    """
    from openai import AzureOpenAI
    import os
    
    with tracer.start_as_current_span("direct_openai_comparison") as span:
        try:
            client = AzureOpenAI(
                api_version="2024-12-01-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            )
            
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What's the difference between agents and direct API calls?"}
                ],
                max_tokens=150
            )
            
            print(f"🔄 Direct OpenAI Response: {response.choices[0].message.content}")
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Direct OpenAI call failed: {e}")
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return None

# Example usage
if __name__ == "__main__":
    try:
        # Your agent ID
        AGENT_ID = "asst_kuYwsFLKl36IQOI5nNc2kgFn"
        
        print("🚀 Testing Agent Conversations with Enhanced Tracing...")
        
        # Test conversation 1 - with manual input/output capture
        result1 = run_agent_conversation_with_tracing(
            agent_id=AGENT_ID,
            user_message="Hi Nurse - How are you ?",
            conversation_name="greeting_conversation_enhanced"
        )
        
        time.sleep(2)
        
        # Test conversation 2 - different topic
        result2 = run_agent_conversation_with_tracing(
            agent_id=AGENT_ID,
            user_message="What do you think of my health?",
            conversation_name="capabilities_inquiry_enhanced"
        )
        
        time.sleep(2)
        
        # Compare with direct OpenAI call (this will automatically get input/output traced)
        print("\n🔄 Running direct OpenAI call for comparison...")
        direct_result = run_direct_openai_call_for_comparison()
        
        print(f"\n📊 Completed all traced conversations!")
        print("✅ Agent conversations now have manual input/output tracing")
        print("✅ Direct OpenAI calls have automatic input/output tracing")
        print("Check your Azure AI Foundry Tracing dashboard - Input/Output columns should now be populated!")
        
    except Exception as e:
        print(f"❌ Error running conversations: {e}")