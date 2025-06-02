# Twin DataPond

<div align="center">

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Digital Twin](https://img.shields.io/badge/Digital-Twin-0078D4?style=for-the-badge&logo=microsoft)
![Data Pipeline](https://img.shields.io/badge/Data-Pipeline-FF6B6B?style=for-the-badge&logo=apache-airflow)
![MobileX](https://img.shields.io/badge/MobileX-Cluster-4CAF50?style=for-the-badge&logo=kubernetes)

*Comprehensive Digital Twin Data Infrastructure on Kubernetes*

</div>

## 🚀 Overview

Twin DataPond is a collection of **Kubernetes YAML configurations** used during master's degree research and deployment phases. This repository contains all the YAML files used in the master's thesis research:

**"Design and Implementation of Cloud-native Digital Twin Service Cluster"**

The configurations range from actively used production deployments to deprecated experimental setups, serving as both a working toolkit and historical reference for digital twin infrastructure development.

> **🔄 Repository Status:**  
> This repository primarily serves for **lab team knowledge transfer and reference**. While it contains practical deployment configurations, it's designed more for internal team handover than professional external use.

> **🔄 Repository Evolution:**  
> This repository is currently being reorganized and may be reclassified with a new name in the future to better reflect its expanded scope.

### ✨ Repository Characteristics

- **📚 Master's Research Archive**: Complete collection of YAML files from thesis research
- **🔄 Mixed Status**: Contains both actively used and deprecated configurations  
- **🏗️ Infrastructure as Code**: K8S deployment configurations for digital twin services
- **🎓 Knowledge Transfer**: Designed for lab team handover and reference
- **📊 Historical Reference**: Documentation of cloud-native digital twin cluster evolution

## 🏗️ Repository Structure

```
twin-datapond/
├── 📁 kubernetes/                    # K8S Deployment YAMLs
│   ├── Infra Deployment ~~/
├── 📁 examples/                      # Example Code & Experiments
├── 📁 docs/                         # Documentation
│   └── wiki/                        # Wiki content
└── 📋 README.md                     # This file
```

## 📂 Component Overview

| Component | Location | Description | Purpose |
|-----------|----------|-------------|---------|
| **🚀 Kubernetes YAMLs** | `kubernetes/` | Complete deployment configurations and test YAMLs for K8S | Production & testing deployment |
| **💡 Example Code** | `examples/` | Experimental code and usage examples independent of K8S deployment | Learning & development |
| **📚 Documentation** | `docs/wiki/` | Comprehensive usage guides and deployment instructions | Reference & tutorials |

## 🛠️ Quick Start

### Prerequisites

- **Kubernetes Cluster**: Access to MobileX cluster
- **kubectl**: Kubernetes command-line tool configured
- **Lab Access**: Internal lab network access required

### Usage Notes

> **⚠️ Important:** These configurations contain specific IP addresses and settings from the original research environment. Review and modify according to your deployment requirements.

### Basic Deployment

Currently, general lab members are only permitted to deploy Pods within the name-twin namespace.
For namespace rules or deployment permissions on the upcoming TwinX Cluster, please contact PhD student Kangryul Kim.

1. **Clone Repository**
   ```bash
   git clone https://github.com/SmartX-Team/twin-datapond.git
   cd twin-datapond
   ```

2. **Configure Environment**


   ```bash
   # To deploy to the existing MobileX Cluster, please contact the cluster administrator, Ho Kim, for access tokens and login credentials.
   # You need login Key Cloak (MobileX Cluster Created Kim Ho)
   ```

3. **Deploy Core Services**
   ```bash
   # Deploy base infrastructure
   kubectl apply -f kubernetes/*.yaml
   
   # Deploy services
   kubectl apply -f kubernetes/services/
   ```

4. **Verify Deployment**
   ```bash
   # Check pod status
   kubectl get pods -n name-twin
   
   # Check services
   kubectl get services -n name-twin
   ```

## 🔧 Configuration Management

### Security Considerations

> **🛡️ Security Notice:**  
> While our research lab operates on a completely internal network, this repository contains exposed IP addresses and passwords. We considered making it private but maintain public access for easier reference and team handover. 
> 
> **Future Plans:** When the new TwinX Cluster construction is complete and new deployments begin, IP rules will be clearly established.

### Configuration Files

- **Historical Context**: Configurations from master's degree research period
- **Mixed Status**: Some actively used, others deprecated
- **Lab Reference**: Designed for internal team knowledge transfer

### Environment Setup

```bash
# Example configuration
export CLUSTER_NAME="mobilex-cluster"
export NAMESPACE="twin-datapond"
export DATA_PIPELINE_VERSION="v1.0.0"
```

## 🎓 Research Context

This repository contains all Kubernetes YAML configurations used in the master's thesis:

**"Design and Implementation of Cloud-native Digital Twin Service Cluster"**

### Research Artifacts

- **Production YAMLs**: Configurations that were actively used during research
- **Experimental Setups**: Test configurations and proof-of-concept deployments  
- **Deprecated Components**: Historical configurations kept for reference
- **Infrastructure Evolution**: Documentation of cluster development over time

## 📝 Usage Guidelines

### For Lab Team Members

1. **Review Configuration Status**: Check if configurations are still active or deprecated
2. **Modify IP Settings**: Update IP addresses and credentials for your environment  
3. **Test Carefully**: Verify configurations in development environment first
4. **Document Changes**: Keep track of modifications for future reference

### For External Users

> **Note:** This repository is primarily designed for internal lab team handover. External users should use these configurations as reference and adapt them to their specific environments.

## 📚 Documentation & Wiki

Comprehensive documentation is available in the repository wiki:

- **Deployment Guides**: Step-by-step deployment instructions
- **Configuration References**: Detailed parameter explanations
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Recommended patterns and approaches

> **📖 Wiki Access:**  
> Visit the repository wiki for detailed usage instructions and deployment guides.

## 🔄 Development Workflow

### Testing New Configurations

1. **Use Testing YAMLs**
   ```bash
   # Test configurations before production
   kubectl apply -f kubernetes/testing/
   ```

2. **Validate Deployment**
   ```bash
   # Check resource status
   kubectl describe pods -n twin-datapond
   ```

3. **Monitor Logs**
   ```bash
   # View service logs
   kubectl logs -f deployment/twin-datapond -n twin-datapond
   ```

### Contributing New Examples

1. **Add Example Code** to `examples/` directory
2. **Include Documentation** in relevant README files
3. **Test Thoroughly** in testing environment
4. **Submit Pull Request** with detailed description

## 🛡️ Security & Access

### MobileX Cluster Security

- **Network Isolation**: External access blocked by default
- **IP/Port Protection**: Direct exposure poses minimal risk
- **Configuration Security**: Avoid exposing sensitive data in code
- **Access Control**: Cluster access permissions required

### Best Practices

- Use ConfigMaps for non-sensitive configuration
- Leverage Kubernetes Secrets for sensitive data
- Implement proper RBAC policies
- Regular security audits and updates

## 🔄 Migration & Evolution

### Planned Changes

- **Repository Reorganization**: Future reclassification planned
- **Enhanced Documentation**: Expanded wiki content
- **Improved Examples**: More comprehensive example code
- **Better Integration**: Enhanced third-party integrations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SmartX Research Lab** - For providing research environment and infrastructure
- **Master's Thesis Research** - Foundation for cloud-native digital twin cluster design
- **Kubernetes Community** - For the robust container orchestration platform
- **Lab Team Members** - For collaborative development and knowledge sharing

---

<div align="center">

**📚 Repository for lab team knowledge transfer and research reference**

*Preserving digital twin infrastructure knowledge for future research*

</div>