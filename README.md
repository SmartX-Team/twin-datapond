# twin-datapond
처음 twin-datapond 및 Data Pipeline 를 K8S 에 배포할때 사용한 yaml 들 모음이었는데, 현재는 Digital Twin Service를 위한 전반적인 인프라 YAML 들과 예제 코드를 포함하여 정리중인 Repository이다.  
나중에 Repository 명을 변경해서 재분류 예정 

kubernetes Folder : 배포할때 사용한 yaml 및 테스트용으로 사용해본 yaml 파일들 모두 포함되어 있습니다. 사용법은 WIKI 에
examples : 쿠버네티스 위에 직접 배포와는 상관없이 여러 실험용 테스트 및 사용법을 같이 정리해둔 코드입니다.

twin-datapond was initially a collection of YAMLs used for deploying twin-datapond and Data Pipeline to K8S. Currently, it is being reorganized as a repository that includes overall infrastructure YAMLs and example codes for Digital Twin Service.

Planning to reclassify later by changing the Repository name

***

![twin-datapond](https://github.com/user-attachments/assets/4a5134a1-a5fb-4c61-94d7-d1352ef3e541)

[Digital Twin 컨셉]

***

! MobileX Cluster 가 외부 접속은 기본적으로 차단되어있어서 IP 나 Port가 직접 노출되도 크게 문제 생길일은 적으나 가급적 보안키 정도라도 코드상에 노출되지 않도록 조심해주세요
config 파일은 MatterMost 디지털 트윈 채널로 공유중 다만 파일이 버전따라서 내용이 다를 수 있으니 만약 찾을 수 없다면 따로 문의 
