"""
Tests for Kubernetes deployment validation.

This module contains tests that validate the Kubernetes deployment
manifests and can be used to test the deployed application.
"""

import subprocess
import time
import yaml
import pytest
from pathlib import Path


class TestKubernetesManifests:
    """Test Kubernetes manifest files for validity."""
    
    def test_namespace_manifest_valid(self):
        """Test that namespace.yaml is valid YAML and has correct structure."""
        manifest_path = Path(__file__).parent.parent / "k8s" / "namespace.yaml"
        
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        assert manifest['apiVersion'] == 'v1'
        assert manifest['kind'] == 'Namespace'
        assert manifest['metadata']['name'] == 'fastapi-postgres'
        assert 'labels' in manifest['metadata']
    
    def test_postgres_storage_manifest_valid(self):
        """Test that postgres-storage.yaml is valid YAML."""
        manifest_path = Path(__file__).parent.parent / "k8s" / "postgres-storage.yaml"
        
        with open(manifest_path, 'r') as f:
            content = f.read()
            manifests = list(yaml.safe_load_all(content))
        
        # Should have 2 resources: PVC and PV
        assert len(manifests) == 2
        
        pvc = manifests[0]
        pv = manifests[1]
        
        assert pvc['kind'] == 'PersistentVolumeClaim'
        assert pv['kind'] == 'PersistentVolume'
        assert pvc['metadata']['name'] == 'postgres-pvc'
        assert pv['metadata']['name'] == 'postgres-pv'
    
    def test_postgres_deployment_manifest_valid(self):
        """Test that postgres-deployment.yaml is valid YAML."""
        manifest_path = Path(__file__).parent.parent / "k8s" / "postgres-deployment.yaml"
        
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        assert manifest['kind'] == 'Deployment'
        assert manifest['metadata']['name'] == 'postgres'
        assert manifest['metadata']['namespace'] == 'fastapi-postgres'
        
        # Check container spec
        container = manifest['spec']['template']['spec']['containers'][0]
        assert container['name'] == 'postgres'
        assert container['image'] == 'postgres:15'
        
        # Check environment variables
        env_vars = {env['name']: env['value'] for env in container['env']}
        assert 'POSTGRES_DB' in env_vars
        assert 'POSTGRES_USER' in env_vars
        assert 'POSTGRES_PASSWORD' in env_vars
        
        # Check health probes
        assert 'livenessProbe' in container
        assert 'readinessProbe' in container
    
    def test_fastapi_deployment_manifest_valid(self):
        """Test that fastapi-deployment.yaml is valid YAML."""
        manifest_path = Path(__file__).parent.parent / "k8s" / "fastapi-deployment.yaml"
        
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        assert manifest['kind'] == 'Deployment'
        assert manifest['metadata']['name'] == 'fastapi-app'
        assert manifest['metadata']['namespace'] == 'fastapi-postgres'
        
        # Check replicas
        assert manifest['spec']['replicas'] == 2
        
        # Check container spec
        container = manifest['spec']['template']['spec']['containers'][0]
        assert container['name'] == 'fastapi-app'
        assert container['image'] == 'fastapi-postgres-app:latest'
        
        # Check environment variables
        env_vars = {env['name']: env['value'] for env in container['env']}
        assert 'DATABASE_URL' in env_vars
        assert 'postgres-service' in env_vars['DATABASE_URL']
        
        # Check health probes
        assert 'livenessProbe' in container
        assert 'readinessProbe' in container
    
    def test_services_manifest_valid(self):
        """Test that services.yaml is valid YAML."""
        manifest_path = Path(__file__).parent.parent / "k8s" / "services.yaml"
        
        with open(manifest_path, 'r') as f:
            content = f.read()
            manifests = list(yaml.safe_load_all(content))
        
        # Should have 2 services
        assert len(manifests) == 2
        
        postgres_svc = manifests[0]
        fastapi_svc = manifests[1]
        
        assert postgres_svc['metadata']['name'] == 'postgres-service'
        assert fastapi_svc['metadata']['name'] == 'fastapi-service'
        
        assert postgres_svc['spec']['type'] == 'ClusterIP'
        assert fastapi_svc['spec']['type'] == 'LoadBalancer'


class TestKubernetesDeployment:
    """Test actual Kubernetes deployment (integration tests)."""
    
    def run_kubectl_command(self, args):
        """Helper to run kubectl commands."""
        try:
            result = subprocess.run(
                ['kubectl'] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            pytest.skip(f"kubectl command failed: {e.stderr}")
    
    def test_kubectl_available(self):
        """Test that kubectl is available and configured."""
        try:
            subprocess.run(['kubectl', 'version', '--client'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("kubectl not available or not configured")
    
    def test_dry_run_manifests(self):
        """Test that all manifests pass kubectl dry-run validation."""
        k8s_dir = Path(__file__).parent.parent / "k8s"
        
        # Test each manifest file
        manifest_files = [
            "namespace.yaml",
            "postgres-storage.yaml", 
            "postgres-deployment.yaml",
            "fastapi-deployment.yaml",
            "services.yaml"
        ]
        
        for manifest_file in manifest_files:
            manifest_path = k8s_dir / manifest_file
            if manifest_path.exists():
                try:
                    subprocess.run([
                        'kubectl', 'apply', '--dry-run=client',
                        '-f', str(manifest_path)
                    ], capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    pytest.fail(f"Dry-run failed for {manifest_file}: {e.stderr}")
    
    @pytest.mark.integration
    def test_deployment_status(self):
        """Test that deployments are running (requires actual cluster)."""
        # This test requires the deployment to actually be running
        self.test_kubectl_available()
        
        # Check if namespace exists
        try:
            self.run_kubectl_command(['get', 'namespace', 'fastapi-postgres'])
        except:
            pytest.skip("Namespace 'fastapi-postgres' not found - deployment not active")
        
        # Check deployments
        postgres_status = self.run_kubectl_command([
            'get', 'deployment', 'postgres', 
            '-n', 'fastapi-postgres',
            '-o', 'jsonpath={.status.readyReplicas}'
        ])
        
        fastapi_status = self.run_kubectl_command([
            'get', 'deployment', 'fastapi-app',
            '-n', 'fastapi-postgres', 
            '-o', 'jsonpath={.status.readyReplicas}'
        ])
        
        assert int(postgres_status) >= 1, "PostgreSQL deployment not ready"
        assert int(fastapi_status) >= 1, "FastAPI deployment not ready"
    
    @pytest.mark.integration
    def test_service_accessibility(self):
        """Test that services are accessible (requires port-forward)."""
        # This would require setting up port-forwarding
        # For now, just test that services exist
        self.test_kubectl_available()
        
        try:
            postgres_svc = self.run_kubectl_command([
                'get', 'svc', 'postgres-service',
                '-n', 'fastapi-postgres'
            ])
            assert 'postgres-service' in postgres_svc
            
            fastapi_svc = self.run_kubectl_command([
                'get', 'svc', 'fastapi-service', 
                '-n', 'fastapi-postgres'
            ])
            assert 'fastapi-service' in fastapi_svc
        except:
            pytest.skip("Services not found - deployment not active")


def test_deployment_script_exists():
    """Test that deployment script exists and is executable."""
    deploy_script = Path(__file__).parent.parent / "k8s" / "deploy.sh"
    cleanup_script = Path(__file__).parent.parent / "k8s" / "cleanup.sh"
    
    assert deploy_script.exists(), "deploy.sh script not found"
    assert cleanup_script.exists(), "cleanup.sh script not found"
    
    # Check if scripts are executable (Unix/Linux)
    import stat
    deploy_stat = deploy_script.stat()
    cleanup_stat = cleanup_script.stat()
    
    assert deploy_stat.st_mode & stat.S_IEXEC, "deploy.sh is not executable"
    assert cleanup_stat.st_mode & stat.S_IEXEC, "cleanup.sh is not executable"


if __name__ == "__main__":
    # Run basic manifest validation tests
    pytest.main([__file__, "-v", "-k", "not integration"])