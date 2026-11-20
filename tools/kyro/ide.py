"""Generate IntelliJ IDEA shared run configurations for all Minecraft loader targets."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

IMPLEMENTED = {
    ('1.18.2', 'forge'),
    ('1.18.2', 'fabric'),
    ('1.19.2', 'forge'),
    ('1.19.2', 'fabric'),
    ('1.19.4', 'forge'),
    ('1.19.4', 'fabric'),
    ('1.20', 'forge'),
    ('1.20', 'fabric'),
    ('1.20.1', 'forge'),
    ('1.20.1', 'fabric'),
    ('1.20.2', 'forge'),
    ('1.20.2', 'fabric'),
    ('1.20.2', 'neoforge'),
    ('1.20.3', 'forge'),
    ('1.20.3', 'fabric'),
    ('1.20.3', 'neoforge'),
    ('1.20.4', 'forge'),
    ('1.20.4', 'fabric'),
    ('1.20.4', 'neoforge'),
    ('1.20.5', 'fabric'),
    ('1.20.5', 'neoforge'),
    ('1.20.6', 'forge'),
    ('1.20.6', 'fabric'),
    ('1.20.6', 'neoforge'),
    ('1.21', 'forge'),
    ('1.21', 'fabric'),
    ('1.21', 'neoforge'),
    ('1.21.1', 'forge'),
    ('1.21.1', 'fabric'),
    ('1.21.1', 'neoforge'),
    ('1.21.2', 'fabric'),
    ('1.21.2', 'neoforge'),
    ('1.21.3', 'forge'),
    ('1.21.3', 'fabric'),
    ('1.21.3', 'neoforge'),
    ('1.21.4', 'forge'),
    ('1.21.4', 'fabric'),
    ('1.21.4', 'neoforge'),
}

def generate_run_configurations():
    run_dir = ROOT / '.run'
    run_dir.mkdir(parents=True, exist_ok=True)
    idea_run_dir = ROOT / '.idea' / 'runConfigurations'
    idea_run_dir.mkdir(parents=True, exist_ok=True)

    targets_file = ROOT / 'targets.json'
    targets = json.loads(targets_file.read_text(encoding='utf-8'))['targets']

    created = 0
    for target in targets:
        mc = target['minecraft']
        mc_clean = mc.replace('.', '_')
        for loader in target['loaders'].keys():
            flags = ""

            name = f"runClient - {mc} ({loader})"
            file_name = f"runClient_{mc_clean}_{loader}.run.xml"
            direct_task = f"runClient_{mc_clean}_{loader}"

            xml_content = f'''<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="{name}" type="GradleRunConfiguration" factoryName="Gradle">
    <ExternalSystemSettings>
      <option name="executionName" />
      <option name="externalProjectPath" value="$PROJECT_DIR$" />
      <option name="externalSystemIdString" value="GRADLE" />
      <option name="scriptParameters" value="{flags}" />
      <option name="taskDescriptions">
        <list />
      </option>
      <option name="taskNames">
        <list>
          <option value="{direct_task}" />
        </list>
      </option>
      <option name="vmOptions" />
    </ExternalSystemSettings>
    <ExternalSystemDebugServerProcess>true</ExternalSystemDebugServerProcess>
    <ExternalSystemReRunDebugProcess>true</ExternalSystemReRunDebugProcess>
    <DebugAllEnabled>false</DebugAllEnabled>
    <method v="2" />
  </configuration>
</component>
'''
            (run_dir / file_name).write_text(xml_content, encoding='utf-8')
            (idea_run_dir / file_name).write_text(xml_content, encoding='utf-8')
            created += 1

    print(f"Generated {created} IntelliJ IDEA run configurations in {run_dir} and {idea_run_dir}")
    return created

if __name__ == '__main__':
    generate_run_configurations()
